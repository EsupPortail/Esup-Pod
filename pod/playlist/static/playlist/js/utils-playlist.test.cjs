/**
 * @file Esup-Pod tests for playlist utilities
 * Prevent regressions in utils-playlist.js
 */

const assert = require("node:assert/strict");
const fs = require("node:fs");
const test = require("node:test");
const vm = require("node:vm");
const { FakeButton } = require("../../../../test-utils.cjs");

const source = fs.readFileSync(
  new URL("./utils-playlist.js", `file://${__dirname}/`),
  "utf8",
);

// Load preventRefreshButton in an isolated context.
function loadPreventRefreshButton(fetchMock, logger = console) {
  const context = {
    fetch: fetchMock,
    console: logger,
    document: {},
    DOMParser: class {},
    window: { setTimeout },
    gettext: (text) => text,
  };
  vm.runInNewContext(
    `${source}; this.preventRefreshButton = preventRefreshButton;`,
    context,
  );
  return context.preventRefreshButton;
}

// Trigger a click listener and wait for the asynchronous response handling.
async function clickButton(button) {
  await button.listeners.get("click").call(button, { preventDefault() {} });
}

test("preventRefreshButton toggles the playlist button after JSON responses", async () => {
  const requestedUrls = [];
  const states = ["in-playlist", "out-playlist"];
  const preventRefreshButton = loadPreventRefreshButton(async (url) => {
    requestedUrls.push(url);
    return { ok: true, json: async () => ({ state: states.shift() }) };
  });
  const button = new FakeButton({
    classes: [
      "action-btn",
      "btn-success",
      "add-video-from-playlist",
    ],
    attributes: {
      href: "/playlist/add/video/",
      title: "Add the video in this playlist",
      "aria-label": "Add the video in this playlist",
    },
    iconClasses: ["bi", "bi-plus"],
  });

  preventRefreshButton(button, true);
  await clickButton(button);

  assert.deepEqual(requestedUrls, ["/playlist/add/video/?json=true"]);
  assert.equal(button.getAttribute("href"), "/playlist/remove/video/?json=true");
  assert.equal(button.icon.contains("bi-plus"), false);
  assert.equal(button.icon.contains("bi-dash"), true);
  assert.equal(button.classList.contains("btn-danger"), true);
  assert.equal(
    button.getAttribute("title"),
    "Remove the video from this playlist",
  );
  assert.equal(
    button.getAttribute("aria-label"),
    "Remove the video from this playlist",
  );

  await clickButton(button);
  assert.deepEqual(requestedUrls, [
    "/playlist/add/video/?json=true",
    "/playlist/remove/video/?json=true",
  ]);
  assert.equal(button.getAttribute("href"), "/playlist/add/video/?json=true");
  assert.equal(button.icon.contains("bi-dash"), false);
  assert.equal(button.icon.contains("bi-plus"), true);
  assert.equal(button.classList.contains("btn-success"), true);
  assert.equal(button.getAttribute("title"), "Add the video in this playlist");
  assert.equal(button.getAttribute("aria-label"), "Add the video in this playlist");
  assert.equal(button.replacedWith, null);
});

test("favorite JSON responses update stars and accessible labels", async () => {
  const states = ["in-playlist", "out-playlist"];
  const preventRefreshButton = loadPreventRefreshButton(async () => ({
    ok: true, json: async () => ({ state: states.shift() }),
  }));
  const button = new FakeButton({
    classes: ["favorite-btn-link"],
    attributes: { href: "/playlist/add/favorites/video/", "aria-pressed": "false" },
    iconClasses: ["bi", "bi-star"],
  });
  preventRefreshButton(button, true);
  await clickButton(button);
  assert.equal(button.icon.contains("bi-star-fill"), true);
  assert.equal(button.icon.contains("bi-star"), false);
  assert.equal(button.icon.contains("bi-dash"), false);
  assert.equal(button.getAttribute("aria-pressed"), "true");
  assert.equal(button.getAttribute("title"), "Remove from favorite");
  await clickButton(button);
  assert.equal(button.icon.contains("bi-star"), true);
  assert.equal(button.icon.contains("bi-star-fill"), false);
  assert.equal(button.icon.contains("bi-plus"), false);
  assert.equal(button.getAttribute("aria-pressed"), "false");
  assert.equal(button.getAttribute("aria-label"), "Add in favorite");
});

test("failed requests restore the modal button and allow retrying", async () => {
  let attempts = 0;
  const errors = [];
  const preventRefreshButton = loadPreventRefreshButton(async () => ({
    ok: ++attempts > 1,
    json: async () => ({ state: "in-playlist" }),
  }), { error: (...args) => errors.push(args) });
  const url = "/playlist/add/playlist/video/";
  const button = new FakeButton({
    classes: ["action-btn", "btn-success"],
    attributes: { href: url },
    iconClasses: ["bi", "bi-plus"],
  });
  preventRefreshButton(button, true);
  await clickButton(button);
  assert.equal(errors.length, 1);
  assert.equal(button.classList.contains("disabled"), false);
  assert.equal(button.getAttribute("href"), url);
  await clickButton(button);
  assert.equal(attempts, 2);
  assert.equal(button.icon.contains("bi-dash"), true);
});
