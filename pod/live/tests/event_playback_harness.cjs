/**
 * @file Esup-Pod event playback harness with controlled media events and timers.
 */
const fs = require("node:fs");
const vm = require("node:vm");
const input = JSON.parse(fs.readFileSync(0, "utf8"));
const elements = Object.fromEntries(
  ["divvideoplayer", "divvideoonhold", "podvideoplayer", "podvideoonholdplayer"].map(
    (id) => [id, { id, style: { display: id === "divvideoonhold" ? "none" : "block" } }],
  ),
);
const players = {};
const timers = new Map();
const documentHandlers = {};
let nextTimer = 0;
let runnerCallbacks;
const errors = [];

/**
 * Create or reuse a Video.js test player and record its media interactions.
 * @param {string|Object} id Player element ID or DOM-like test element.
 * @param {Object} options Options passed by the rendered event script.
 * @returns {Object} Mock player with event, media and modal state.
 */
function videojs(id, options) {
  id = typeof id === "string" ? id : id?.id;
  if (!elements[id]) throw new Error(`Missing player element: ${id}`);
  if (players[id]) return players[id];
  const handlers = {};
  const player = {
    sources: [], modals: [], pauses: 0, plays: 0, viewerCounts: 0,
    options, handlers,
    on(events, callback) {
      for (const event of Array.isArray(events) ? events : [events]) {
        (handlers[event] ||= []).push(callback);
      }
    },
    trigger(event) { for (const callback of handlers[event] || []) callback(); },
    videoJsLogo() {},
    videoJsViewerCount() { this.viewerCounts++; },
    pause() { this.pauses++; },
    play() { this.plays++; return Promise.resolve(); },
    src(source) {
      this.sources.push(source);
      if (!source || !source.length && !source.src) errors.push("MEDIA_ERR_SRC_NOT_SUPPORTED");
    },
    // A failed source selection can leave both of these empty.
    currentSrc() { return ""; },
    currentType() { return ""; },
    createModal() {
      const modal = {
        closed: false,
        close() { this.closed = true; },
        dispose() { this.close(); },
      };
      this.modals.push(modal);
      return modal;
    },
    dispose() {
      delete elements[id];
      if (id === "divvideoonhold") delete elements.podvideoonholdplayer;
      delete players[id];
    },
  };
  players[id] = player;
  return player;
}
videojs.getPlayer = (id) => players[id];
videojs.Hls = videojs.Vhs = { xhr: {} };
const context = {
  videojs,
  window: { PodRunnerLive: { start(player, callbacks) { runnerCallbacks = callbacks; } } },
  document: {
    getElementById: (id) => elements[id] || null,
    addEventListener(event, callback) { documentHandlers[event] = callback; },
  },
  console: { info() {}, warn() {}, error() {}, log() {} },
  location: { reload() {} },
  fetch: async () => ({ ok: true, json: async () => ({ content: "" }) }),
  setTimeout(callback, ms) {
    const id = ++nextTimer;
    timers.set(id, { callback, ms });
    return id;
  },
  clearTimeout(id) { timers.delete(id); },
  setInterval() {},
};
vm.runInNewContext(input.script, context);
const snapshots = [];
for (const action of input.actions) {
  if (action === "dom") documentHandlers.DOMContentLoaded();
  else if (action === "retry") {
    const timer = [...timers].find(([, value]) => value.ms === 10000);
    if (!timer) throw new Error("No pending retry");
    timers.delete(timer[0]);
    timer[1].callback();
  } else if (action === "runner-unavailable") runnerCallbacks.onUnavailable();
  else if (action === "runner-available") runnerCallbacks.onAvailable();
  else players.podvideoplayer.trigger(action);
  snapshots.push({
    liveDisplay: elements.divvideoplayer?.style.display,
    waitingDisplay: elements.divvideoonhold?.style.display,
    pendingRetries: [...timers.values()].filter((timer) => timer.ms === 10000).length,
    liveSources: [...(players.podvideoplayer?.sources || [])],
    waitingSources: [...(players.podvideoonholdplayer?.sources || [])],
    waitingPauses: players.podvideoonholdplayer?.pauses || 0,
    waitingPlays: players.podvideoonholdplayer?.plays || 0,
    openWaitingModals: players.podvideoonholdplayer?.modals.filter((modal) => !modal.closed).length || 0,
    viewerCounts: players.podvideoplayer?.viewerCounts || 0,
    liveLoop: players.podvideoplayer?.options.loop,
    errors: [...errors],
  });
}
process.stdout.write(JSON.stringify(snapshots));
