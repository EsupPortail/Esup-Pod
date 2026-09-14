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

// Simulate cards, bubbling clicks and the DOM replacement performed by InfiniteLoader.
function createCardScenario(favorites, responses = [true]) {
  const requests = [];
  const errors = [];
  const listeners = new Map();
  const title = new FakeButton();
  const updatedTitle = { textContent: "Updated video count" };
  const list = {
    cards: [],
    get innerHTML() {
      return this.cards.map((card) => `${card.id},`).join("");
    },
    set innerHTML(value) {
      this.cards = value.split(",").filter(Boolean).map(createCard);
    },
  };

  // Supply the card selectors and ancestor lookup used by the real click handlers.
  function createCard(id) {
    const card = {
      id,
      removed: false,
      buttons: [],
      querySelector: (selector) => card.buttons.find((button) =>
        button.classList.contains(selector.slice(1))) || null,
      remove: () => { card.removed = true; },
    };
    for (const isFavorite of favorites ? [true] : [false, true]) {
      const button = new FakeButton({
        classes: ["remove-from-playlist-btn-link", ...(isFavorite ? ["favorite-btn-link"] : [])],
        attributes: {
          href: `/playlist/remove/${isFavorite ? "favorites" : "custom"}/video-${id}/`,
          "data-csrf-token": "card-token",
          ...(!isFavorite || favorites ? { "data-remove-playlist-card": "true" } : {}),
        },
        iconClasses: ["bi", isFavorite ? "bi-star-fill" : "bi-folder-minus"],
      });
      button.closest = (selector) => {
        if (selector === ".draggable-container") return card;
        if (selector === "#videos_list [data-remove-playlist-card]") {
          return list.cards.includes(card) && button.getAttribute("data-remove-playlist-card") ? button : null;
        }
        throw new Error(`Unexpected ancestor selector: ${selector}`);
      };
      card.buttons.push(button);
    }
    return card;
  }

  list.cards.push(createCard("1"));
  const context = loadPlaylistContext(async (url, options) => {
    requests.push({ url, options });
    if (options.method === "GET") return { text: async () => "page-two" };
    const ok = responses.length > 1 ? responses.shift() : responses[0];
    return { ok, text: async () => "updated", json: async () => ({ state: "out-playlist" }) };
  }, { error: (...args) => errors.push(args) }, {
    document: {
      addEventListener: (event, listener) => {
        if (!listeners.has(event)) listeners.set(event, []);
        listeners.get(event).push(listener);
      },
      getElementsByClassName: (name) => name === "draggable-container" ? list.cards
        : list.cards.flatMap((card) => card.buttons.filter((button) => button.classList.contains(name))),
      getElementById: (id) => ({ videos_list: list, video_count: title })[id] || null,
      querySelector: () => ({ style: {} }),
      querySelectorAll: () => [],
    },
    DOMParser: class {
      parseFromString(data) {
        return {
          getElementById: (id) => id === "videos_list"
            ? { innerHTML: data === "page-two" ? "2," : "", dataset: { nextpage: "false" } }
            : updatedTitle,
        };
      }
    },
    window: { addEventListener() {}, removeEventListener() {} },
    hideEmptyDropdowns() {},
  });
  vm.runInContext(fs.readFileSync(`${__dirname}/video-playlists-remove-card.js`, "utf8"), context);
  if (!favorites) {
    vm.runInContext(fs.readFileSync(`${__dirname}/video-list-favorites-card.js`, "utf8"), context);
  }
  for (const listener of listeners.get("DOMContentLoaded") || []) listener();

  return {
    list, requests, errors, title, updatedTitle,
    // Execute the real pagination loader, including its favorite-button initialization.
    async loadNextPage() {
      const infiniteSource = fs.readFileSync(`${__dirname}/../../../../main/static/js/infinite.js`, "utf8");
      vm.runInContext(`${infiniteSource}; this.InfiniteLoader = InfiniteLoader;`, context);
      let loader;
      const loaded = new Promise((resolve) => {
        loader = new context.InfiniteLoader("/playlist/custom/?page=", () => {}, resolve);
      });
      await loader.initMore();
      await loaded;
    },
    // Bubble an icon click through the button and document before awaiting the handlers.
    async click(button) {
      const event = {
        defaultPrevented: false,
        target: { closest: (selector) => button.closest(selector) },
        preventDefault() { this.defaultPrevented = true; },
      };
      const pending = [];
      const handler = button.listeners.get("click");
      if (handler) pending.push(handler.call(button, event));
      for (const listener of listeners.get("click") || []) pending.push(listener(event));
      await Promise.all(pending);
      return event;
    },
  };
}

for (const favorites of [false, true]) {
  const label = favorites ? "Favorites" : "Playlist";
  test(`${label} removes both earlier and new cards after infinite pagination`, async () => {
    const scenario = createCardScenario(favorites);
    await scenario.loadNextPage();
    assert.equal(scenario.list.cards.length, 2);
    for (const card of scenario.list.cards) {
      const event = await scenario.click(card.buttons[0]);
      assert.equal(event.defaultPrevented, true);
      assert.equal(card.removed, true);
      assert.equal(scenario.title.replacedWith, scenario.updatedTitle);
    }
    const mutations = scenario.requests.filter(({ options }) => options.method === "POST");
    assert.equal(mutations.length, 2);
    for (const { url, options } of mutations) {
      assertPostOptions(options, "card-token");
      assert.equal(url.includes("?json"), false);
    }
    assert.deepEqual(scenario.errors, []);
  });

  test(`${label} keeps a card after a refused POST and allows retrying`, async () => {
    const scenario = createCardScenario(favorites, [false, true]);
    const card = scenario.list.cards[0];
    const button = card.buttons[0];
    await scenario.click(button);
    assert.equal(card.removed, false);
    assert.equal(scenario.title.replacedWith, null);
    assert.equal(button.classList.contains("disabled"), false);
    assert.equal(scenario.errors.length, 1);
    await scenario.click(button);
    assert.equal(card.removed, true);
    assert.equal(scenario.requests.length, 2);
    scenario.requests.forEach(({ options }) => assertPostOptions(options, "card-token"));
  });

  test(`${label} sends only one request for repeated clicks during removal`, async () => {
    const scenario = createCardScenario(favorites);
    const card = scenario.list.cards[0];
    await Promise.all([scenario.click(card.buttons[0]), scenario.click(card.buttons[0])]);
    assert.equal(scenario.requests.length, 1);
    assertPostOptions(scenario.requests[0].options, "card-token");
    assert.equal(card.removed, true);
    assert.deepEqual(scenario.errors, []);
  });
}

test("a paginated favorite toggle in a custom playlist leaves the card visible", async () => {
  const scenario = createCardScenario(false);
  await scenario.loadNextPage();
  const card = scenario.list.cards[1];
  const button = card.buttons[1];
  await scenario.click(button);
  const mutations = scenario.requests.filter(({ options }) => options.method === "POST");
  assert.equal(mutations.length, 1);
  assertPostOptions(mutations[0].options, "card-token");
  assert.equal(card.removed, false);
  assert.equal(scenario.title.replacedWith, null);
  assert.equal(button.icon.contains("bi-star"), true);
  assert.deepEqual(scenario.errors, []);
});
