/** Run with: node --test pod/video/tests/video_upload.test.cjs */
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
const core = template.match(/<script id="video-upload-core">([\s\S]*?)<\/script>/)[1]
  .replaceAll("{{ CHUNK_SIZE }}", "4")
  .replaceAll("{{ max_size }}", "1")
  .replaceAll("{{ slug|escapejs }}", "existing-video")
  .replace(/\{% trans (["'])(.*?)\1 %\}/g, (match, quote, text) => text)
  .replace(/\{% url 'video:api_chunked_upload_complete' %\}/g, "/complete/")
  .replace(/\{% url 'video:api_chunked_upload' %\}/g, "/upload/")
  .replace(/\{%[^%]*%\}/g, "");
const diagnostics = fs.readFileSync(path.join(__dirname, "../static/js/video_upload.js"), "utf8");
const flush = () => new Promise((resolve) => setImmediate(resolve));

/** Exercise the inline upload independently of optional diagnostic listeners. */
function setup({ missing = false, initError = false, renderError = false, translationError = false, noStatus = false } = {}) {
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
      elements.set(id, {
        value: "", checked: true, disabled: false, textContent: "", style: {}, handlers: {},
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
        addEventListener(name, callback) { this.handlers[name] = callback; },
      });
    }
    return elements.get(id);
  }
  element("submitVideo").disabled = true;
  element("select-transcript-lang").value = "fr";
  element("csrf").value = "csrf-token";

  const document = {
    getElementById: (id) => id === "upload-status" && noStatus ? null : element(id),
    getElementsByName: () => [element("csrf")],
    getElementsByClassName: () => [],
    body: element("body"),
    addEventListener() {},
  };
  const $ = (target) => {
    const wrapper = {
      fileupload(value) { options = value; return wrapper; },
      on(name, selector, callback) {
        if (target === document && initError) throw new Error("Broken diagnostics initialization");
        listeners.push({ name: name.split(".")[0], callback: callback || selector });
        return wrapper;
      },
    };
    return wrapper;
  };
  $.ajax = (request) => completions.push(request);

  function emit(name, data) {
    const event = {
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
    jQuery: $, location: { href: "http://localhost/video/add/" },
    gettext(message) {
      if (translationError) throw new Error("Broken optional translation");
      return message;
    },
  };
  const context = vm.createContext({
    window, document, $, jQuery: $, location: window.location,
    File: Blob, FileReader: Reader, SparkMD5, URL,
    gettext: (message) => message,
    showalert(message) { alerts.push(message); },
  });
  vm.runInContext(core, context);
  if (!missing) vm.runInContext(diagnostics, context);

  return {
    element, context, requests, completions, alerts, reads, window,
    get options() { return options; },
    emit,
    loadDiagnostics() { vm.runInContext(diagnostics, context); },
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
    submit() { element("uploadForm").handlers.submit({ preventDefault() {} }); },
    reset() { element("resetButton").handlers.click(); },
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
    finalError(code = 500, url = "/complete/") {
      for (const listener of listeners) {
        if (listener.name === "ajaxError") listener.callback({}, { status: code }, { url });
      }
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
    upload.completions[0].success({ redirlink: "/video/edit/" });
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
  assert.equal(upload.completions[0].timeout, undefined);
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
  upload.finalError();
  assert.match(upload.element("upload-status").textContent, /Check your dashboard/);
  assert.equal(upload.completions.length, 1);
  upload.finalError(500, "/another-endpoint/");
  assert.equal(upload.completions.length, 1);
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
