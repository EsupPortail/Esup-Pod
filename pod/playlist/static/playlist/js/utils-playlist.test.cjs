/**
 * @file Esup-Pod tests for playlist utilities
 * Prevent regressions in utils-playlist.js
 */

const assert = require("node:assert/strict");
const fs = require("node:fs");
const test = require("node:test");
const vm = require("node:vm");

const source = fs.readFileSync(
  new URL("./utils-playlist.js", `file://${__dirname}/`),
  "utf8",
);

class FakeClassList {
  constructor(...classes) {
    this.classes = new Set(classes);
  }

  contains(className) {
    return this.classes.has(className);
  }

  add(className) {
    this.classes.add(className);
  }

  remove(...classNames) {
    classNames.forEach((className) => this.classes.delete(className));
  }
}

class FakeButton {
  constructor() {
    this.classList = new FakeClassList(
      "action-btn",
      "btn-success",
      "add-video-from-playlist",
    );
    this.attributes = new Map([
      ["href", "/playlist/add/video/"],
      ["title", "Add the video in this playlist"],
      ["aria-label", "Add the video in this playlist"],
    ]);
    this.listeners = new Map();
    this.icon = new FakeClassList("bi", "bi-plus");
    this.style = {};
  }

  addEventListener(eventName, listener) {
    this.listeners.set(eventName, listener);
  }

  getAttribute(name) {
    return this.attributes.get(name) ?? null;
  }

  setAttribute(name, value) {
    this.attributes.set(name, value);
  }

  removeAttribute(name) {
    this.attributes.delete(name);
  }

  querySelector(selector) {
    return selector === ".bi" ? { classList: this.icon } : null;
  }

  replaceWith() {
    throw new Error("The JSON response must not replace the button");
  }
}

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
  assert.equal(button.getAttribute("title"), "Remove video from this playlist");
  assert.equal(
    button.getAttribute("aria-label"),
    "Remove video from this playlist",
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
