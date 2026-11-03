/**
 * Esup-Pod upload and optional diagnostics tests.
 * Run with: node --test pod/video/tests/video_upload.test.cjs
 */
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { createHash } = require("node:crypto");

/** Match the SparkMD5 API used by uploads without requiring browser dependencies. */
const SparkMD5 = {
  ArrayBuffer: class {
    constructor() { this.checksum = createHash("md5"); }
    append(buffer) { this.checksum.update(Buffer.from(buffer)); return this; }
    end() { return this.checksum.digest("hex"); }
  },
  hash(contents) { return createHash("md5").update(contents).digest("hex"); },
};

const template = fs.readFileSync(path.join(__dirname, "../templates/videos/add_video.html"), "utf8");
const core = (transcript) => template.match(/<script id="video-upload-core">([\s\S]*?)<\/script>/)[1]
  .replaceAll("{{ CHUNK_SIZE }}", "4")
  .replaceAll("{{ max_size }}", "1")
  .replaceAll("{{ slug|escapejs }}", "existing-video")
  .replace(/\{% trans (["'])(.*?)\1 %\}/g, (match, quote, text) => text)
  .replace(/\{% url 'video:api_chunked_upload_complete' %\}/g, "/complete/")
  .replace(/\{% url 'video:api_chunked_upload' %\}/g, "/upload/")
  .replace(/\{% if TRANSCRIPT\|length > 0 %\}([\s\S]*?)\{% endif %\}/g, transcript ? "$1" : "")
  .replace(/\{%[^%]*%\}/g, "");
const diagnostics = fs.readFileSync(path.join(__dirname, "../static/js/video_upload.js"), "utf8");
const flush = () => new Promise((resolve) => setImmediate(resolve));

/** Provide the browser CustomEvent API on Node versions without it. */
class CustomEvent extends Event {
  constructor(type, options) {
    super(type, options);
    this.detail = options.detail;
  }
}

/** Exercise the inline upload independently of optional diagnostic listeners. */
function setup({ missing = false, initError = false, renderError = false, translationError = false, noStatus = false, eventError = false, transcript = true } = {}) {
  const elements = new Map();
  const listeners = [];
  const reads = [];
  const requests = [];
  const completions = [];
  const alerts = [];
  let options;

  function element(id) {
    if (!elements.has(id)) {
      const classes = new Set();
      elements.set(id, Object.assign(new EventTarget(), {
        value: "", checked: true, disabled: false, textContent: "", style: {},
        accept: ".mp4, .mov", dataset: { completeUrl: "/complete/" },
        classList: {
          add(name) { classes.add(name); },
          remove(name) { classes.delete(name); },
          contains(name) { return classes.has(name); },
          toggle(name, enabled) {
            if (renderError && id === "upload-status") throw new Error("Broken optional UI");
            if (enabled) classes.add(name); else classes.delete(name);
          },
        },
        addEventListener(name, callback) {
          if (initError && name === "pod-upload-status") throw new Error("Broken diagnostics initialization");
          EventTarget.prototype.addEventListener.call(this, name, callback);
        },
        dispatchEvent(event) {
          if (eventError && event.type === "pod-upload-status") throw new Error("Broken optional event");
          return EventTarget.prototype.dispatchEvent.call(this, event);
        },
      }));
    }
    return elements.get(id);
  }
  element("submitVideo").disabled = true;
  element("select-transcript-lang").value = "fr";
  element("csrf").value = "csrf-token";

  const document = {
    getElementById: (id) => (id === "upload-status" && noStatus) || (id === "select-transcript-lang" && !transcript) ? null : element(id),
    getElementsByName: () => [element("csrf")],
    getElementsByClassName: () => [],
    body: element("body"),
    addEventListener() {},
  };
  const $ = () => {
    const wrapper = {
      fileupload(value) { options = value; return wrapper; },
      on(names, callback) {
        for (const name of names.split(/\s+/)) listeners.push({ name, callback });
        return wrapper;
      },
    };
    return wrapper;
  };
  $.ajax = () => { throw new Error("Upload confirmation must use fetch"); };

  function emit(name, data) {
    const event = {
      type: name,
      preventDefault() { throw new Error("Diagnostics must not cancel upload events"); },
      stopPropagation() { throw new Error("Diagnostics must not stop upload events"); },
    };
    for (const listener of listeners) {
      if (listener.name === name) assert.notEqual(listener.callback(event, data), false);
    }
  }

  class Reader {
    readAsArrayBuffer(blob) { reads.push({ reader: this, blob }); }
  }
  const window = {
    location: { href: "http://localhost/video/add/" },
    gettext(message) {
      if (translationError) throw new Error("Broken optional translation");
      return message;
    },
  };
  const context = vm.createContext({
    window, document, $, jQuery: $, location: window.location,
    File: Blob, FileReader: Reader, SparkMD5, URLSearchParams, CustomEvent,
    fetch(url, options) {
      return new Promise((resolve, reject) => {
        completions.push({ url, options, data: Object.fromEntries(options.body), resolve, reject });
      });
    },
    gettext: (message) => message,
    showalert(message) { alerts.push(message); },
  });
  vm.runInContext(core(transcript), context);
  if (!missing) vm.runInNewContext(diagnostics, { window, document });

  return {
    element, context, requests, completions, alerts, reads, window,
    get options() { return options; },
    emit,
    loadDiagnostics() { vm.runInNewContext(diagnostics, { window, document }); },
    select(contents = "testtest", name = "video.mp4") {
      const file = new Blob([contents]);
      file.name = name;
      const data = {
        files: [file], originalFiles: [file],
        submit() {
          emit("fileuploadsend", this);
          requests.push({ ...this, fields: options.formData.map((field) => ({ ...field })) });
        },
      };
      emit("fileuploadadd", data);
      options.add.call(element("chunked_upload"), {}, data);
      return data;
    },
    submit() { element("uploadForm").dispatchEvent(new Event("submit", { cancelable: true })); },
    reset() { element("resetButton").dispatchEvent(new Event("click")); },
    async read() {
      const { reader, blob } = reads.shift();
      reader.onload({ target: { result: await blob.arrayBuffer() } });
      await flush();
    },
    async prepare() { while (reads.length) await this.read(); },
    async readError() {
      reads.shift().reader.onerror(new Error("Unreadable file"));
      await flush();
    },
    chunk(offset = 4) {
      const data = { ...requests.at(-1), loaded: offset, total: requests.at(-1).files[0].size,
        result: { upload_id: "upload-1", offset } };
      emit("fileuploadchunkdone", data);
      options.chunkdone({}, data);
    },
    async done() {
      const data = { ...requests.at(-1), result: { upload_id: "upload-1" } };
      emit("fileuploaddone", data);
      options.done({}, data);
      await flush();
    },
    fail(code) {
      emit("fileuploadfail", { ...requests.at(-1), jqXHR: { status: code } });
    },
    async complete() {
      completions.at(-1).resolve({ ok: true, json: async () => ({ redirlink: "/video/edit/" }) });
      await flush();
    },
    async finalError(code = 500) {
      completions.at(-1).resolve({ ok: false, status: code });
      await flush();
    },
  };
}

for (const [name, fault] of [
  ["available", {}],
  ["missing (script not loaded)", { missing: true }],
  ["unable to initialize", { initError: true }],
  ["unable to render messages", { renderError: true }],
  ["unable to translate messages", { translationError: true }],
  ["without a status element", { noStatus: true }],
  ["unable to dispatch notifications", { eventError: true }],
]) {
  test(`the original upload completes when diagnostics are ${name}`, async () => {
    const upload = setup(fault);
    upload.select("test");
    assert.equal(upload.element("submitVideo").disabled, false);
    upload.submit();
    assert.equal(upload.requests.length, 1); // MD5 preparation never delays upload start.
    await upload.prepare();
    await upload.done();
    assert.equal(upload.completions.length, 1);
    assert.equal(upload.completions[0].data.md5, "098f6bcd4621d373cade4e832627b4f6");
    assert.equal(upload.completions[0].data.csrfmiddlewaretoken, "csrf-token");
    assert.equal(upload.completions[0].data.slug, "existing-video");
    assert.equal(upload.completions[0].data.transcript, "fr");
    assert.equal(upload.completions[0].url, "/complete/");
    assert.equal(upload.completions[0].options.method, "POST");
    assert.equal(upload.completions[0].options.credentials, "same-origin");
    assert.equal(upload.completions[0].options.headers["X-Requested-With"], "XMLHttpRequest");
    assert.ok(upload.completions[0].options.body instanceof URLSearchParams);
    await upload.complete();
    assert.equal(upload.window.location.href, "/video/edit/");
  });
}

test("a fast transfer waits for its own MD5 only at final validation", async () => {
  const upload = setup();
  upload.select("test");
  upload.submit();
  await upload.done();
  assert.equal(upload.requests.length, 1);
  assert.equal(upload.completions.length, 0);
  await upload.prepare();
  assert.equal(upload.completions.length, 1);
  assert.equal(upload.completions[0].data.md5, SparkMD5.hash("test"));
});

test("changing selection cannot use the previous file's checksum", async () => {
  const upload = setup({ missing: true });
  upload.select("old!");
  upload.reset();
  upload.select("test");
  upload.submit();
  await upload.done();
  await upload.read();
  assert.equal(upload.completions.length, 0);
  await upload.prepare();
  assert.equal(upload.completions[0].data.md5, SparkMD5.hash("test"));
});

test("file reads stay chunked and errors never send an empty checksum", async () => {
  const upload = setup();
  upload.select("testtest");
  assert.equal(upload.reads[0].blob.size, 4);
  upload.submit();
  await upload.readError();
  await upload.done();
  assert.equal(upload.completions.length, 0);
  assert.match(upload.alerts.at(-1), /Unable to read/);
});

test("checksum initialization errors do not prevent selecting or starting the upload", async () => {
  const upload = setup();
  const file = new Blob(["test"]);
  file.name = "video.mp4";
  const data = { files: [file], originalFiles: [file], submit() { upload.requests.push(data); } };
  const original = SparkMD5.ArrayBuffer;
  try {
    SparkMD5.ArrayBuffer = function () { throw new Error("Checksum unavailable"); };
    upload.options.add.call(upload.element("chunked_upload"), {}, data);
    upload.submit();
    await flush();
    assert.equal(upload.requests.length, 1);
    assert.equal(upload.completions.length, 0);
  } finally {
    SparkMD5.ArrayBuffer = original;
  }
});

test("the same chunk settings, upload ID and progress are preserved without diagnostics", async () => {
  const upload = setup({ missing: true });
  upload.select();
  upload.submit();
  assert.equal(upload.options.url, "/upload/");
  assert.equal(upload.options.maxChunkSize, 4);
  assert.equal(upload.options.timeout, undefined);
  assert.equal(upload.options.uploadedBytes, undefined);
  upload.chunk(4);
  assert.equal(upload.options.formData.find((field) => field.name === "upload_id").value, "upload-1");
  assert.equal(upload.element("progBar").value, 50);
  assert.doesNotThrow(() => JSON.stringify(upload.requests.at(-1)));
  await upload.prepare();
  await upload.done();
  assert.equal(upload.completions[0].options.timeout, undefined);
});

test("network errors are observed without retries, timeouts or changes to controls", async () => {
  const upload = setup();
  upload.select();
  upload.submit();
  upload.fail(0);
  assert.match(upload.element("upload-status").textContent, /An error/);
  assert.equal(upload.element("submitVideo").disabled, false);
  assert.equal(upload.requests.length, 1);
  assert.equal(upload.completions.length, 0);
  assert.equal(upload.options.fail, undefined);
  assert.equal(upload.options.submit, undefined);
  assert.equal(upload.options.send, undefined);
  await flush();
  assert.equal(upload.requests.length, 1);
});

test("a diagnostic render failure during an upload error cannot throw into the transport", () => {
  const upload = setup({ renderError: true });
  upload.select();
  upload.submit();
  assert.doesNotThrow(() => upload.fail(500));
  assert.equal(upload.requests.length, 1);
});

test("completion errors are displayed without sending another request", async () => {
  const upload = setup();
  upload.select();
  upload.submit();
  await upload.prepare();
  await upload.done();
  await upload.finalError();
  assert.match(upload.element("upload-status").textContent, /Check your dashboard/);
  assert.equal(upload.completions.length, 1);
});

for (const failure of ["network", "invalid JSON", "authentication"]) {
  test(`a completion ${failure} error is displayed without redirecting or retrying`, async () => {
    const upload = setup();
    upload.select("test");
    upload.submit();
    await upload.prepare();
    await upload.done();
    if (failure === "network") {
      upload.completions[0].reject(new Error("Offline"));
    } else if (failure === "invalid JSON") {
      upload.completions[0].resolve({ ok: true, json: async () => { throw new SyntaxError("Invalid JSON"); } });
    } else {
      upload.completions[0].resolve({ ok: false, status: 403 });
    }
    await flush();
    assert.match(upload.element("upload-status").textContent, /Check your dashboard/);
    assert.equal(upload.element("upload-status").classList.contains("text-danger"), true);
    assert.equal(upload.window.location.href, "http://localhost/video/add/");
    assert.equal(upload.completions.length, 1);
    assert.equal(upload.requests.length, 1);
  });
}

test("native diagnostics show upload phases without access to jQuery", async () => {
  const upload = setup();
  upload.select("test");
  assert.equal(upload.element("upload-status").textContent, "");
  upload.submit();
  assert.equal(upload.element("upload-status").textContent, "Uploading…");
  await upload.prepare();
  await upload.done();
  assert.equal(upload.element("upload-status").textContent, "Checking your upload…");
});

for (const code of [401, 403]) {
  test(`an upload HTTP ${code} error is reported and reset clears the diagnostic`, () => {
    const upload = setup();
    upload.select();
    upload.submit();
    upload.fail(code);
    assert.match(upload.element("upload-status").textContent, /no longer authenticated/);
    assert.equal(upload.element("upload-status").classList.contains("text-danger"), true);
    upload.reset();
    assert.equal(upload.element("upload-status").textContent, "");
    assert.equal(upload.element("upload-status").classList.contains("text-danger"), false);
  });
}

test("completion encodes form values and works without the optional transcript selector", async () => {
  const upload = setup({ transcript: false });
  upload.context.slug = "video with spaces & plus+";
  upload.context.csrf = "token+&=";
  upload.select("test");
  upload.submit();
  await upload.prepare();
  await upload.done();
  assert.equal(upload.completions[0].data.slug, "video with spaces & plus+");
  assert.equal(upload.completions[0].data.csrfmiddlewaretoken, "token+&=");
  assert.equal(Object.hasOwn(upload.completions[0].data, "transcript"), false);
  await upload.complete();
  assert.equal(upload.window.location.href, "/video/edit/");
});

test("diagnostics loaded after upload starts still observe completion", async () => {
  const upload = setup({ missing: true });
  upload.select("test");
  upload.submit();
  upload.loadDiagnostics();
  await upload.prepare();
  await upload.done();
  assert.equal(upload.element("upload-status").textContent, "Checking your upload…");
  await upload.complete();
  assert.equal(upload.window.location.href, "/video/edit/");
});

test("loading diagnostics twice cannot submit or complete twice", async () => {
  const upload = setup();
  upload.loadDiagnostics();
  upload.select();
  upload.submit();
  await upload.prepare();
  await upload.done();
  assert.equal(upload.requests.length, 1);
  assert.equal(upload.completions.length, 1);
});

test("legal notice and extension checks stay in the existing upload core", () => {
  const upload = setup({ missing: true });
  upload.select("test", "video.exe");
  upload.submit();
  assert.equal(upload.requests.length, 0);
  upload.select("test");
  upload.element("legal_notice").checked = false;
  upload.submit();
  assert.equal(upload.requests.length, 0);
  assert.match(upload.alerts.at(-1), /authorizations/);
});

test("file names remain text even without diagnostics", () => {
  const upload = setup({ missing: true });
  const name = '<img src=x onerror="alert(1)">.mp4';
  upload.select("test", name);
  assert.equal(upload.element("file_name").textContent, name);
});
