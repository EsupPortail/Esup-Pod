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

// Load playlist utilities in an isolated context with optional DOM replacements.
function loadPlaylistContext(fetchMock, logger = console, overrides = {}) {
  const context = {
    fetch: fetchMock,
    console: logger,
    document: {},
    DOMParser: class {},
    window: { setTimeout },
    gettext: (text) => text,
    ...overrides,
  };
  vm.createContext(context);
  vm.runInContext(source, context);
  return context;
}

// Return the button listener installer for focused utility tests.
function loadPreventRefreshButton(fetchMock, logger = console) {
  return loadPlaylistContext(fetchMock, logger).preventRefreshButton;
}

// Verify that a mutation sends its rendered token only to the current origin.
function assertPostOptions(options, token) {
  assert.equal(options.method, "POST");
  assert.equal(options.mode, "same-origin");
  assert.equal(options.headers["X-CSRFToken"], token);
}

// Trigger a click listener and wait for the asynchronous response handling.
async function clickButton(button) {
  await button.listeners.get("click").call(button, { preventDefault() {} });
}

test("preventRefreshButton toggles the playlist button after JSON responses", async () => {
  const requestedUrls = [];
  const states = ["in-playlist", "out-playlist"];
  const preventRefreshButton = loadPreventRefreshButton(async (url, options) => {
    assertPostOptions(options, "modal-token");
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
      "data-csrf-token": "modal-token",
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

test("favorite HTML responses preserve POST behavior after replacing the button", async () => {
  const buttons = ["add", "remove", "add"].map((action, index) => {
    const button = new FakeButton({
      classes: ["favorite-btn-link"],
      attributes: {
        href: `/playlist/${action}/favorites/video/`,
        "data-csrf-token": `token-${index}`,
      },
    });
    button.id = "favorite-button";
    return button;
  });
  const requests = [];
  let responseIndex = 0;
  const context = loadPlaylistContext(async (url, options) => {
    assertPostOptions(options, `token-${responseIndex}`);
    requests.push(url);
    return { ok: true, text: async () => "<html></html>" };
  }, console, {
    document: {
      getElementById: (id) => id === "favorite-button" ? buttons[0] : null,
    },
    DOMParser: class {
      parseFromString() {
        return { getElementById: () => buttons[++responseIndex] };
      }
    },
  });
  context.preventRefreshButton(buttons[0], false);
  await clickButton(buttons[0]);
  assert.equal(buttons[0].replacedWith, buttons[1]);
  await clickButton(buttons[1]);
  assert.equal(buttons[1].replacedWith, buttons[2]);
  assert.deepEqual(requests, [
    "/playlist/add/favorites/video/",
    "/playlist/remove/favorites/video/",
  ]);
});

for (const [filename, selector] of [
  ["video-playlists-remove-card.js", ".remove-from-playlist-btn-link"],
  ["video-favorites-remove-card.js", ".favorite-btn-link"],
]) {
  for (const ok of [true, false]) {
    test(`${filename} ${ok ? "removes the card after POST" : "keeps the card after a refused POST"}`, async () => {
      const button = new FakeButton({ attributes: {
        href: "/playlist/remove/playlist/video/",
        "data-csrf-token": "card-token",
      } });
      let removed = false;
      const requests = [];
      const errors = [];
      const title = new FakeButton();
      const updatedTitle = {};
      const card = {
        querySelector: (query) => query === selector ? button : null,
        remove: () => { removed = true; },
      };
      const context = loadPlaylistContext(async (url, options) => {
        requests.push({ url, options });
        return { ok, text: async () => "<html></html>" };
      }, { error: (...args) => errors.push(args) }, {
        document: {
          addEventListener: (event, listener) => {
            assert.equal(event, "DOMContentLoaded");
            listener();
          },
          getElementsByClassName: () => [card, { querySelector: () => null }],
          getElementById: () => title,
        },
        DOMParser: class {
          parseFromString() {
            return { getElementById: () => updatedTitle };
          }
        },
      });
      vm.runInContext(fs.readFileSync(`${__dirname}/${filename}`, "utf8"), context);
      await clickButton(button);
      assert.equal(requests.length, 1);
      assert.equal(requests[0].url, button.getAttribute("href"));
      assertPostOptions(requests[0].options, "card-token");
      assert.equal(removed, ok);
      assert.equal(title.replacedWith, ok ? updatedTitle : null);
      assert.equal(errors.length, ok ? 0 : 1);
    });
  }
}
