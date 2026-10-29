/**
 * @file Esup-Pod tests for automatic Esup-Runner Live playback polling.
 * Run with: node --test pod/live/tests/runner_live.test.cjs
 */
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const script = fs.readFileSync(path.join(__dirname, "../static/js/runner_live.js"), "utf8");
/** Build a ready session with the exact URL expected by the mocked player. */
const ready = (id = "live-1", url = "https://media.example.com/live-1/master.m3u8") => ({
  live_id: id, state: "running", hls_ready: true, hls_url: url,
});
/** Let asynchronous fetch and player callbacks settle before assertions. */
const flush = () => new Promise((resolve) => setImmediate(resolve));

/** Create a mocked player, fetch responses and timers for a polling scenario. */
async function setup(responses, options = {}) {
  const status = {
    hidden: true, textContent: "", classList: { toggle() {} },
    dataset: {
      streamUrl: "/live/event/1-live/?stream=1", waitingMessage: "Waiting for the live stream.",
      startingMessage: "The live stream is starting.", hlsWaitingMessage: "HLS is not ready yet.",
      endedMessage: "The live stream has ended.", failedMessage: "The live stream failed.",
      unavailableMessage: "Live unavailable.", mixedContentMessage: "HTTP on an HTTPS page.",
      playbackErrorMessage: "Unable to play the live stream.", pollingErrorMessage: "Unable to check availability.",
      autoplayMessage: "Press Play to start playback.",
    },
  };
  const timers = new Map();
  const handlers = {};
  const pageHandlers = {};
  const requests = [];
  const sources = [];
  const diagnostics = [];
  const callbacks = { available: 0, unavailable: 0 };
  let nextTimer = 0;
  let currentSrc = "";
  let resets = 0;
  const player = {
    src(source) { sources.push(source); currentSrc = source.src; },
    currentSrc() { return currentSrc; },
    play() { return options.play ? options.play() : Promise.resolve(); },
    /** Return a media error whose private message must never enter diagnostics. */
    error() { return options.playerError || { code: 2, message: "private player URL" }; },
    pause() {},
    reset() { resets++; currentSrc = ""; },
    on(event, handler) { handlers[event] = handler; },
    off(event) { delete handlers[event]; },
  };
  const window = {
    location: { protocol: options.protocol || "https:" },
    addEventListener(event, handler) { pageHandlers[event] = handler; },
    removeEventListener(event) { delete pageHandlers[event]; },
  };
  vm.runInNewContext(script, {
    window, document: { getElementById: () => status }, AbortController, URL,
    console: { warn(message, details) { diagnostics.push({ message, details }); } },
    setTimeout(callback, ms) { const id = ++nextTimer; timers.set(id, { callback, ms }); return id; },
    clearTimeout(id) { timers.delete(id); },
    fetch(url, options) {
      requests.push({ url, options });
      const value = responses.shift();
      if (typeof value === "function") return value(options);
      if (value instanceof Error) return Promise.reject(value);
      return Promise.resolve({ ok: value?.ok !== false, status: value?.status || 200, redirected: value?.redirected, json: async () => value });
    },
  });
  const stop = window.PodRunnerLive.start(player, {
    onAvailable() { callbacks.available++; },
    onUnavailable() { callbacks.unavailable++; },
  });
  await flush();
  return {
    status, player, sources, requests, callbacks, handlers, pageHandlers, timers, stop, diagnostics,
    get resets() { return resets; },
    /** Dispatch a page lifecycle event and wait for asynchronous work to settle. */
    async dispatchPageEvent(event, persisted) {
      if (pageHandlers[event]) pageHandlers[event]({ persisted });
      await flush();
    },
    /** Fire the next scheduled timeout and wait for its asynchronous callbacks. */
    async tick(ms = 5000) {
      const timer = [...timers].find(([, value]) => value.ms === ms);
      assert.ok(timer, `Expected timer at ${ms} ms`);
      timers.delete(timer[0]);
      timer[1].callback();
      await flush();
    },
  };
}

test("an open page waits for HLS, clears stopped HLS, and follows a new session", async () => {
  const live = await setup([
    { live_id: null, state: "waiting_source", hls_ready: false, hls_url: null },
    { ...ready(), hls_ready: false }, ready(),
    { ...ready(), state: "completed" }, ready("live-2", "https://media.example.com/live-2/master.m3u8?exact=1"),
  ]);
  assert.equal(live.sources.length, 0);
  assert.equal(live.status.hidden, false);
  await live.tick();
  assert.equal(live.sources.length, 0);
  await live.tick();
  assert.equal(live.sources[0].src, ready().hls_url);
  assert.equal(live.status.hidden, true);
  await live.tick();
  assert.equal(live.player.currentSrc(), "");
  assert.equal(live.resets, 1);
  assert.equal(live.status.hidden, false);
  await live.tick();
  assert.equal(live.sources[1].src, "https://media.example.com/live-2/master.m3u8?exact=1");
  assert.equal(live.status.hidden, true);
  for (const request of live.requests) {
    assert.equal(request.url, "/live/event/1-live/?stream=1");
    assert.equal(request.options.cache, "no-store");
    assert.equal(request.options.credentials, "same-origin");
    assert.equal(request.options.headers.Authorization, undefined);
  }
});

test("stable playback is retained and a changed session or URL replaces the source", async () => {
  const live = await setup([ready(), ready(), ready("live-2"), ready("live-2", "https://media.example.com/new/master.m3u8")]);
  await live.tick();
  assert.equal(live.sources.length, 1);
  await live.tick();
  assert.equal(live.sources.length, 2);
  await live.tick();
  assert.equal(live.sources.length, 3);
});

test("network and server failures preserve playback and polling continues", async () => {
  const live = await setup([ready(), new Error("offline"), { ok: false, status: 503 }, ready("live-2")]);
  await live.tick();
  assert.equal(live.player.currentSrc(), ready().hls_url);
  assert.equal(live.status.hidden, true);
  await live.tick(10000);
  assert.equal(live.sources.length, 1);
  assert.equal(live.resets, 0);
  await live.tick(10000);
  assert.equal(live.sources.length, 2);
});

test("a player error retains HLS for a subsequent playback retry", async () => {
  const live = await setup([ready(), ready()]);
  live.handlers.error();
  assert.equal(live.player.currentSrc(), ready().hls_url);
  assert.equal(live.resets, 0);
  assert.equal(live.status.hidden, false);
  assert.equal(live.status.dataset.diagnostic, "playback_error");
  assert.equal(live.diagnostics[0].details.media_error_code, 2);
  assert.ok(!JSON.stringify(live.diagnostics).includes("private player URL"));
  await live.tick();
  assert.equal(live.sources.length, 2);
  assert.equal(live.status.hidden, false);
  live.handlers.playing();
  assert.equal(live.status.hidden, true);
  assert.equal(live.callbacks.available, 3);
});

test("a secure page explains HTTP HLS without assigning or rewriting its URL", async () => {
  const insecure = ready("live-1", "http://media.example.com/live/master.m3u8?secret=private");
  const live = await setup([insecure, insecure, ready("live-2")]);
  assert.equal(live.sources.length, 0);
  assert.equal(live.status.hidden, false);
  assert.equal(live.status.dataset.diagnostic, "mixed_content");
  assert.equal(live.status.textContent, "HTTP on an HTTPS page.");
  assert.equal(live.diagnostics.length, 1);
  assert.ok(!JSON.stringify(live.diagnostics).includes("secret=private"));
  await live.tick();
  assert.equal(live.diagnostics.length, 1);
  assert.equal(live.sources.length, 0);
  await live.tick();
  assert.equal(live.sources[0].src, ready("live-2").hls_url);
  assert.equal(live.status.hidden, true);
});

test("an HTTP page keeps the manager HTTP HLS URL unchanged", async () => {
  const insecure = ready("live-1", "http://media.example.com/live/master.m3u8?exact=1");
  const live = await setup([insecure], { protocol: "http:" });
  assert.equal(live.sources[0].src, insecure.hls_url);
  assert.equal(live.status.hidden, true);
  assert.equal(live.diagnostics.length, 0);
});

test("successful polling distinguishes completed sessions from unready HLS", async () => {
  const live = await setup([
    { ...ready(), hls_ready: false }, { ...ready(), state: "completed" },
    { ...ready(), state: "starting" }, { ...ready(), state: "failed" },
  ]);
  assert.equal(live.status.dataset.diagnostic, "hls_waiting");
  assert.equal(live.status.textContent, "HLS is not ready yet.");
  await live.tick();
  assert.equal(live.status.dataset.diagnostic, "ended");
  assert.equal(live.status.textContent, "The live stream has ended.");
  await live.tick();
  assert.equal(live.status.dataset.diagnostic, "starting");
  await live.tick();
  assert.equal(live.status.dataset.diagnostic, "failed");
  assert.equal(live.diagnostics[0].details.reason, "failed");
});

test("HTTP polling failures expose only their safe status in diagnostics", async () => {
  const live = await setup([{ ok: false, status: 403, private: "secret" }, ready()]);
  assert.equal(live.status.dataset.diagnostic, "polling_error");
  assert.equal(live.diagnostics[0].details.http_status, 403);
  assert.ok(!JSON.stringify(live.diagnostics).includes("secret"));
  await live.tick();
  assert.equal(live.status.hidden, true);
});

test("blocked autoplay preserves the ready source and asks the user to press Play", async () => {
  const live = await setup([ready(), ready()], {
    play: () => Promise.reject({ name: "NotAllowedError", message: "secret" }),
  });
  assert.equal(live.player.currentSrc(), ready().hls_url);
  assert.equal(live.status.dataset.diagnostic, "autoplay");
  assert.equal(live.status.hidden, false);
  assert.equal(live.diagnostics.length, 0);
  await live.tick();
  assert.equal(live.sources.length, 1);
  assert.equal(live.status.hidden, false);
  live.handlers.playing();
  assert.equal(live.status.hidden, true);
});

test("a timed out request aborts, preserves playback and schedules another check", async () => {
  const live = await setup([ready(), (options) => new Promise((resolve, reject) => {
    options.signal.addEventListener("abort", () => reject(new Error("timeout")));
  }), ready("live-2")]);
  await live.tick();
  await live.tick(30000);
  assert.equal(live.requests[1].options.signal.aborted, true);
  assert.equal(live.player.currentSrc(), ready().hls_url);
  assert.equal(live.resets, 0);
  await live.tick(10000);
  assert.equal(live.sources.length, 2);
});

test("a manager outage has no fixed playback cutoff and a confirmed stop still clears HLS", async () => {
  const unknown = {
    live_id: "live-1", state: "manager_unavailable", hls_ready: false, hls_url: null,
    discovery_status: "unreachable", retryable: true, hls_status: "checking",
  };
  const live = await setup([
    ready(), ...Array.from({ length: 30 }, () => ({ ...unknown })),
    { ...ready(), state: "completed", hls_ready: false, hls_url: null },
  ]);
  await live.tick();
  for (let index = 1; index < 30; index++) await live.tick(10000);
  assert.equal(live.player.currentSrc(), ready().hls_url);
  assert.equal(live.sources.length, 1);
  assert.equal(live.resets, 0);
  assert.equal(live.callbacks.unavailable, 0);
  await live.tick(10000);
  assert.equal(live.player.currentSrc(), "");
  assert.equal(live.resets, 1);
});

test("new viewers wait for HLS confirmation while the manager is unavailable", async () => {
  const live = await setup([
    { state: "manager_unavailable", hls_ready: false, hls_url: null, retryable: true },
    { ...ready(), discovery_status: "error", hls_status: "active", retryable: true },
  ]);
  assert.equal(live.sources.length, 0);
  assert.equal(live.status.hidden, false);
  await live.tick(10000);
  assert.equal(live.player.currentSrc(), ready().hls_url);
  assert.equal(live.status.hidden, true);
});

test("failed media retries its existing URL while manager discovery is down", async () => {
  const live = await setup([ready(), {
    state: "manager_unavailable", hls_ready: false, hls_url: null, retryable: true,
  }]);
  live.handlers.error();
  assert.equal(live.resets, 0);
  await live.tick();
  assert.equal(live.sources.length, 2);
  assert.equal(live.player.currentSrc(), ready().hls_url);
  assert.equal(live.status.hidden, false);
  live.handlers.playing();
  assert.equal(live.status.hidden, true);
  assert.equal(live.callbacks.available, 2);
});

test("access refusals and login redirects clear ongoing playback", async () => {
  for (const failure of [
    { ok: false, status: 401 }, { ok: false, status: 403 },
    { ok: false, status: 404 }, { redirected: true },
    { state: "unavailable", hls_ready: false, hls_url: null, retryable: false },
  ]) {
    const live = await setup([ready(), failure]);
    await live.tick();
    assert.equal(live.player.currentSrc(), "");
    assert.equal(live.resets, 1);
    live.stop();
  }
});

test("a manager outage preserves an outstanding autoplay prompt", async () => {
  const live = await setup([ready(), new Error("offline")], {
    play: () => Promise.reject({ name: "NotAllowedError" }),
  });
  await live.tick();
  assert.equal(live.status.dataset.diagnostic, "autoplay");
  assert.equal(live.status.hidden, false);
  assert.equal(live.player.currentSrc(), ready().hls_url);
  assert.equal(live.resets, 0);
});

test("cached page navigation suspends polling and resumes once per restoration", async () => {
  const live = await setup([ready(), ready(), ready("live-2")]);
  await live.dispatchPageEvent("pageshow", false);
  assert.equal(live.requests.length, 1);

  for (let cycle = 0; cycle < 2; cycle++) {
    await live.dispatchPageEvent("pagehide", true);
    assert.equal(live.timers.size, 0);
    assert.equal(typeof live.handlers.error, "function");
    assert.equal(typeof live.handlers.playing, "function");

    await live.dispatchPageEvent("pageshow", true);
    assert.equal(live.requests.length, cycle + 2);
    assert.equal(live.timers.size, 1);
    await live.dispatchPageEvent("pageshow", true);
    assert.equal(live.requests.length, cycle + 2);
  }
  assert.equal(live.sources.length, 2);
  assert.equal(live.resets, 0);
  live.handlers.error();
  assert.equal(live.status.dataset.diagnostic, "playback_error");
  live.handlers.playing();
  assert.equal(live.status.hidden, true);
  live.stop();
});

test("restoration ignores late responses and errors from an aborted request", async () => {
  for (const rejectRequest of [false, true]) {
    let complete;
    let fail;
    const live = await setup([
      ready(),
      () => new Promise((resolve, reject) => { complete = resolve; fail = reject; }),
      ready("live-2", "https://media.example.com/live-2/master.m3u8"),
      { ...ready("live-2"), state: "completed", hls_ready: false, hls_url: null },
    ]);
    await live.tick();
    await live.dispatchPageEvent("pagehide", true);
    assert.equal(live.requests[1].options.signal.aborted, true);
    await live.dispatchPageEvent("pageshow", true);
    assert.equal(live.requests.length, 3);

    if (rejectRequest) fail(new Error("late failure"));
    else complete({ ok: true, json: async () => ({ state: "completed", hls_ready: false }) });
    await flush();
    assert.equal(live.player.currentSrc(), "https://media.example.com/live-2/master.m3u8");
    assert.equal(live.resets, 0);
    assert.equal(live.timers.size, 1);
    assert.equal(live.status.hidden, true);
    assert.equal(live.diagnostics.length, 0);

    await live.tick();
    assert.equal(live.requests.length, 4);
    assert.equal(live.resets, 1);
    live.stop();
  }
});

test("permanent page closure and explicit stop prevent later restoration", async () => {
  for (const explicitStop of [false, true]) {
    const live = await setup([ready()]);
    if (explicitStop) {
      await live.dispatchPageEvent("pagehide", true);
      live.stop();
    } else await live.dispatchPageEvent("pagehide", false);
    assert.equal(live.timers.size, 0);
    assert.deepEqual(Object.keys(live.pageHandlers), []);
    assert.deepEqual(Object.keys(live.handlers), []);
    await live.dispatchPageEvent("pageshow", true);
    assert.equal(live.requests.length, 1);
  }
});

test("disposal cancels polling and ignores a response still in flight", async () => {
  let complete;
  const live = await setup([() => new Promise((resolve) => { complete = resolve; })]);
  live.handlers.dispose();
  complete({ ok: true, json: async () => ready() });
  await flush();
  assert.equal(live.sources.length, 0);
  assert.equal(live.timers.size, 0);
  assert.equal(live.requests[0].options.signal.aborted, true);
  assert.deepEqual(Object.keys(live.pageHandlers), []);
  assert.deepEqual(Object.keys(live.handlers), []);
});
