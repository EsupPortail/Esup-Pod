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
function loadPreventRefreshButton(fetchMock) {
  const context = {
    fetch: fetchMock,
    console,
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
  await new Promise((resolve) => setTimeout(resolve, 350));
}

test("preventRefreshButton toggles the playlist button after JSON responses", async () => {
  const requestedUrls = [];
  const states = ["in-playlist", "out-playlist"];
  const preventRefreshButton = loadPreventRefreshButton(async (url) => {
    requestedUrls.push(url);
    return { ok: true, json: async () => ({ state: states.shift() }) };
  });
  const button = new FakeButton();

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
});
