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
    document: { addEventListener() {} },
    DOMParser: class {},
    gettext: (text) => text,
    ...overrides,
    window: { setTimeout: (callback) => callback(), ...overrides.window },
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
  assert.equal(options.redirect, "error");
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
  assert.equal(button.getAttribute("href"), "/playlist/remove/video/");
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
  assert.equal(button.getAttribute("href"), "/playlist/add/video/");
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

for (const initiallyFavorite of [false, true]) {
  test(`header stars without the bi class toggle in both directions (initial favorite: ${initiallyFavorite})`, async () => {
    const states = initiallyFavorite ? ["out-playlist", "in-playlist"] : ["in-playlist", "out-playlist"];
    const preventRefreshButton = loadPreventRefreshButton(async () => ({
      ok: true, json: async () => ({ state: states.shift() }),
    }));
    const button = new FakeButton({
      classes: [initiallyFavorite ? "remove-from-playlist-btn-link" : "favorite-btn-link"],
      attributes: {
        href: `/playlist/${initiallyFavorite ? "remove" : "add"}/favorites/video/`,
        "aria-pressed": String(initiallyFavorite),
      },
      iconClasses: [initiallyFavorite ? "bi-star-fill" : "bi-star"],
    });
    button.id = "favorite-button";
    assert.equal(button.querySelector(".bi"), null);
    preventRefreshButton(button);
    for (const favorite of [!initiallyFavorite, initiallyFavorite]) {
      await clickButton(button);
      assert.equal(button.icon.contains("bi-star"), !favorite);
      assert.equal(button.icon.contains("bi-star-fill"), favorite);
      assert.equal(button.icon.contains("bi-plus"), false);
      assert.equal(button.icon.contains("bi-dash"), false);
      assert.equal(button.getAttribute("aria-pressed"), String(favorite));
      assert.equal(button.getAttribute("href"), `/playlist/${favorite ? "remove" : "add"}/favorites/video/`);
      assert.equal(button.getAttribute("aria-label"), favorite ? "Remove from favorite" : "Add in favorite");
    }
  });
}

for (const response of [
  { ok: true, redirected: true, json: async () => ({ state: "in-playlist" }) },
  { ok: true, json: async () => { throw new SyntaxError("Login page HTML"); } },
  { ok: true, json: async () => ({}) },
]) {
  test("unexpected responses leave the favorite unchanged and allow retrying", async () => {
    const errors = [];
    const button = new FakeButton({
      classes: ["favorite-btn-link"],
      attributes: { href: "/playlist/add/favorites/video/", "aria-pressed": "false" },
      iconClasses: ["bi", "bi-star"],
    });
    const install = loadPreventRefreshButton(async () => response, { error: (...args) => errors.push(args) });
    install(button);
    await clickButton(button);
    assert.equal(button.icon.contains("bi-star"), true);
    assert.equal(button.getAttribute("aria-pressed"), "false");
    assert.equal(button.classList.contains("disabled"), false);
    assert.equal(errors.length, 1);
  });
}

// Simulate cards, bubbling clicks and the DOM replacement performed by InfiniteLoader.
function createCardScenario(favorites, responses = [true]) {
  const requests = [];
  const errors = [];
  const listeners = new Map();
  const title = new FakeButton();
  let refreshCount = 0;
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
        if (selector === ".favorite-btn-link, #favorite-button, #playlist-list .action-btn") {
          return isFavorite ? button : null;
        }
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
    if (options.method === "GET") return { ok: true, text: async () => "page-two" };
    const ok = responses.length > 1 ? responses.shift() : responses[0];
    return typeof ok === "object" ? ok : { ok, json: async () => ({ state: "out-playlist" }) };
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
    refreshVideosSearch() { refreshCount++; },
  });
  vm.runInContext(fs.readFileSync(`${__dirname}/video-playlists-remove-card.js`, "utf8"), context);
  if (!favorites) {
    vm.runInContext(fs.readFileSync(`${__dirname}/video-list-favorites-card.js`, "utf8"), context);
  }
  for (const listener of listeners.get("DOMContentLoaded") || []) listener();

  return {
    list, requests, errors, title, updatedTitle,
    get refreshCount() { return refreshCount; },
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
      return loader;
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
      assert.ok(scenario.refreshCount > 0);
    }
    const mutations = scenario.requests.filter(({ options }) => options.method === "POST");
    assert.equal(mutations.length, 2);
    for (const { url, options } of mutations) {
      assertPostOptions(options, "card-token");
      assert.equal(url.endsWith("?json=true"), true);
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

// Run player transitions with fresh controls each time the video fragment is replaced.
function createPlayerScenario(enriched, controls = true, config = {}) {
  const requests = [];
  const errors = [];
  const readyListeners = [];
  const elements = new Map();
  const history = [];
  const videoRequests = [];
  let favoriteButton;
  let modalButton;
  let videoNumber = 1;

  // Recreate controls as innerHTML does, without retaining the old event listeners.
  function replaceControls(number, favorite = false) {
    videoNumber = Number(number);
    favoriteButton = new FakeButton({
      classes: [favorite ? "remove-from-playlist-btn-link" : "favorite-btn-link"],
      attributes: {
        href: `/playlist/${favorite ? "remove" : "add"}/favorites/video-${number}/`,
        "data-csrf-token": `token-${number}`,
      },
      iconClasses: [favorite ? "bi-star-fill" : "bi-star"],
    });
    favoriteButton.id = "favorite-button";
    favoriteButton.replaceWith = (replacement) => { favoriteButton = replacement; };
    modalButton = new FakeButton({
      classes: ["action-btn", "btn-success", "add-video-from-playlist"],
      attributes: { href: `/playlist/add/custom/video-${number}/`, "data-csrf-token": `token-${number}` },
      iconClasses: ["bi", "bi-plus"],
    });
    const modal = {
      children: [{ querySelector: () => modalButton }],
      replaceWith(replacement) { elements.set("playlist-list", replacement); },
    };
    elements.set("playlist-list", controls ? modal : null);
  }

  const playerElement = {
    set innerHTML(content) {
      if (content.startsWith("video-")) replaceControls(content.slice(6));
      else favoriteButton = modalButton = null;
    },
  };
  elements.set("video-player", playerElement);
  elements.set("collapseAside", { appendChild(element) { elements.set(element.id, element); } });
  for (const id of config.initialAside || []) {
    elements.set(id, { id, remove() { elements.delete(id); } });
  }
  elements.set("card-enrichment-informations", { style: {} });
  elements.set("enrichment_style_id", { remove() {} });
  for (const id of ["mainbreadcrumb", "more-script", "title"]) elements.set(id, {});
  const videos = [1, 2, 3].map((number) => {
    const button = new FakeButton({
      classes: ["player-element", ...(number === 1 ? ["selected"] : [])],
      attributes: {
        href: `/video/video-${number}/?playlist=custom`,
        "data-url-for-video": `/playlist/get-video/video-${number}/custom/`,
      },
    });
    button.id = String(number);
    button.querySelector = () => ({ innerHTML: "" });
    return button;
  });
  replaceControls(1);
  const context = loadPlaylistContext(async (url, options) => {
    requests.push({ url, options });
    return {
      ok: true,
      json: async () => ({ state: "in-playlist" }),
      text: async () => `favorite-${videoNumber}`,
    };
  }, { error: (...args) => errors.push(args) }, {
    document: {
      addEventListener: (event, listener) => {
        if (event === "DOMContentLoaded") readyListeners.push(listener);
      },
      getElementById: (id) => id === "favorite-button" ? (controls ? favoriteButton : null) : elements.get(id),
      querySelector: (selector) => selector === ".selected"
        ? videos.find((video) => video.classList.contains("selected"))
        : elements.get(selector.replace(/^#/, "")),
      querySelectorAll: (selector) => selector === ".player-element" ? videos
        : selector === "#playlist-list .action-btn" && controls ? [modalButton] : [],
      createDocumentFragment: () => ({
        appendChild(element) { this.element = element; },
        querySelector() { return this.element; },
      }),
    },
    DOMParser: class {
      parseFromString(content) {
        if (content.startsWith("favorite-")) {
          replaceControls(content.slice(9), true);
          return { getElementById: (id) => id === "favorite-button" ? favoriteButton : elements.get(id) };
        }
        return {
          querySelectorAll: () => [],
          querySelector: (selector) => {
            if (content.startsWith("aside-") && selector !== "#card-enrichment-informations") {
              const ids = config.aside?.[content.slice(6)] || [];
              if (!ids.includes(selector.slice(1))) return null;
            }
            return { id: selector.slice(1), innerHTML: content, cloneNode() { return this; }, remove() { elements.delete(this.id); } };
          },
        };
      }
    },
    XMLHttpRequest: class {
      open(method, url) { this.url = url; }
      send() {
        const number = this.url.match(/video-(\d+)/)[1];
        this.readyState = 4;
        videoRequests.push(this.url);
        this.status = config.status || 200;
        this.responseText = config.response ?? JSON.stringify({
          opengraph: "", breadcrumbs: "", page_aside: `aside-${number}`, more_script: "scripts", page_title: "title",
          page_content: `video-${number}`, enrichment_is_on: enriched,
        });
        this.onreadystatechange();
      }
    },
    MutationObserver: class { observe() {} },
    history: { pushState(_state, _title, url) { history.push(url); } },
    window: { location: { href: "" } },
    setTimeout: (callback) => callback(),
  });
  if (controls) {
    for (const name of ["video-header-favorites.js", "playlist-modal.js"]) {
      vm.runInContext(fs.readFileSync(`${__dirname}/${name}`, "utf8"), context);
    }
  }
  vm.runInContext(fs.readFileSync(`${__dirname}/playlist-player.js`, "utf8"), context);
  readyListeners.forEach((listener) => listener());
  return {
    context, requests, errors, videos, history, elements, videoRequests,
    get favoriteButton() { return favoriteButton; },
    get modalButton() { return modalButton; },
  };
}

for (const enriched of [false, true]) {
  test(`${enriched ? "Enriched" : "Standard"} player rebinds favorites and playlists after each video transition`, async () => {
    const scenario = createPlayerScenario(enriched);
    for (const number of [2, 3]) {
      const previousFavorite = scenario.favoriteButton;
      const previousModal = scenario.modalButton;
      scenario.context.switchToNextVideo();
      assert.notEqual(scenario.favoriteButton, previousFavorite);
      assert.notEqual(scenario.modalButton, previousModal);
      await clickButton(scenario.modalButton);
      await clickButton(scenario.favoriteButton);
      assert.equal(scenario.favoriteButton.icon.contains("bi-star-fill"), true);
      assert.equal(scenario.favoriteButton.icon.contains("bi-star"), false);
      const requests = scenario.requests.slice(-2);
      assert.equal(requests[0].url, `/playlist/add/custom/video-${number}/?json=true`);
      assert.equal(requests[1].url, `/playlist/add/favorites/video-${number}/?json=true`);
      requests.forEach(({ options }) => assertPostOptions(options, `token-${number}`));
      assert.equal(typeof scenario.favoriteButton.listeners.get("click"), "function");
      assert.equal(typeof scenario.modalButton.listeners.get("click"), "function");
    }
    assert.equal(scenario.requests.length, 4);
    assert.deepEqual(scenario.errors, []);
  });
}

test("playlist video transitions also work without favorite or modal controls", () => {
  const scenario = createPlayerScenario(false, false);
  assert.doesNotThrow(() => scenario.context.switchToNextVideo());
  assert.equal(scenario.requests.length, 0);
});

for (const status of [200, 403, 500]) {
  for (const countdown of [0, 5]) {
    test(`autoplay keeps the old player until the next response succeeds (${status}, ${countdown})`, async () => {
      const scenario = createPlayerScenario(false, true, { status });
      let disposals = 0;
      scenario.context.player = { dispose() { disposals++; } };
      scenario.context.playlistCount = countdown;
      await scenario.context.handlePlaylistVideoEnded();
      assert.equal(disposals, status === 200 ? 1 : 0);
      assert.equal(scenario.videos[0].classList.contains("selected"), status !== 200);
    });
  }
}

test("autoplay using a complete page keeps the current player until navigation", async () => {
  const scenario = createPlayerScenario(false);
  scenario.videos[1].setAttribute("data-full-page", "true");
  scenario.context.playlistCount = 0;
  scenario.context.player = { dispose() { assert.fail("Premature disposal"); } };
  await scenario.context.handlePlaylistVideoEnded();
  assert.equal(scenario.context.window.location.href, scenario.videos[1].getAttribute("href"));
  assert.equal(scenario.videoRequests.length, 0);
});

test("filter replacement keeps previously unbound favorite controls usable", async () => {
  const scenario = createCardScenario(false);
  scenario.list.innerHTML = "3,";
  const card = scenario.list.cards[0];
  assert.equal(card.buttons[1].listeners.size, 0);
  await scenario.click(card.buttons[1]);
  assert.equal(scenario.requests.length, 1);
  assertPostOptions(scenario.requests[0].options, "card-token");
  assert.equal(card.removed, false);
  assert.equal(card.buttons[1].icon.contains("bi-star"), true);
});

test("redirected removal responses keep the card and pagination unchanged", async () => {
  const scenario = createCardScenario(true, [{ ok: true, redirected: true }]);
  const card = scenario.list.cards[0];
  await scenario.click(card.buttons[0]);
  assert.equal(card.removed, false);
  assert.equal(scenario.refreshCount, 0);
  assert.equal(scenario.errors.length, 1);
});

test("removing the current player video navigates to the playlist contents", async () => {
  const context = loadPlaylistContext(async () => ({
    ok: true, json: async () => ({ state: "out-playlist" }),
  }), console, { window: { location: { href: "" } } });
  const button = new FakeButton({
    classes: ["action-btn"],
    attributes: { href: "/playlist/remove/custom/video/", "data-removed-url": "/playlist/custom/" },
  });
  context.preventRefreshButton(button);
  await clickButton(button);
  assert.equal(context.window.location.href, "/playlist/custom/");
});

test("the Favorites modal and header stay synchronized after either control is used", async () => {
  const attributes = { href: "/playlist/add/favorites/video/", "data-playlist-id": "1", "data-video-id": "2" };
  const modal = new FakeButton({ classes: ["action-btn"], attributes, iconClasses: ["bi", "bi-plus"] });
  const header = new FakeButton({ classes: ["favorite-btn-link"], attributes, iconClasses: ["bi-star"] });
  header.id = "favorite-button";
  const states = ["in-playlist", "out-playlist"];
  const context = loadPlaylistContext(async () => ({ ok: true, json: async () => ({ state: states.shift() }) }), console, {
    document: { addEventListener() {}, querySelectorAll: () => [modal, header] },
  });
  context.preventRefreshButton(modal);
  context.preventRefreshButton(header);
  await clickButton(modal);
  assert.equal(header.icon.contains("bi-star-fill"), true);
  assert.equal(header.getAttribute("href"), "/playlist/remove/favorites/video/");
  await clickButton(header);
  assert.equal(header.icon.contains("bi-star"), true);
  assert.equal(header.icon.contains("bi-star-fill"), false);
  assert.equal(modal.icon.contains("bi-plus"), true);
  assert.equal(modal.getAttribute("href"), "/playlist/add/favorites/video/");
});

test("reloading utilities and rebinding a button sends only one mutation", async () => {
  let requests = 0;
  const callbacks = [];
  const context = loadPlaylistContext(async () => {
    requests++;
    return { ok: true, json: async () => ({ state: "out-playlist" }) };
  });
  const button = new FakeButton({ attributes: { href: "/playlist/remove/custom/video/" } });
  button.addEventListener = (_event, callback) => callbacks.push(callback);
  context.preventRefreshButton(button);
  vm.runInContext(source, context);
  context.preventRefreshButton(button);
  assert.equal(callbacks.length, 1);
  await callbacks[0].call(button, { preventDefault() {} });
  assert.equal(requests, 1);
});

test("fast successful actions ignore double clicks until feedback has been visible", async () => {
  const requests = [];
  let finishFeedback;
  let signalFeedback;
  const feedbackStarted = new Promise((resolve) => { signalFeedback = resolve; });
  const context = loadPlaylistContext(async (url) => {
    requests.push(url);
    return { ok: true, json: async () => ({ state: "in-playlist" }) };
  }, console, {
    window: {
      setTimeout(callback, delay) {
        assert.equal(delay, 300);
        finishFeedback = callback;
        signalFeedback();
      },
    },
  });
  const button = new FakeButton({
    classes: ["favorite-btn-link"],
    attributes: { href: "/playlist/add/favorites/video/" },
    iconClasses: ["bi", "bi-star"],
  });
  context.preventRefreshButton(button);
  const firstClick = clickButton(button);
  await clickButton(button);
  await feedbackStarted;
  assert.equal(button.icon.contains("bi-star-fill"), true);
  assert.equal(button.classList.contains("disabled"), true);
  await clickButton(button);
  assert.equal(requests.length, 1);
  finishFeedback();
  await firstClick;
  assert.equal(button.classList.contains("disabled"), false);

  const nextClick = clickButton(button);
  assert.equal(requests.length, 2);
  assert.equal(requests[1], "/playlist/remove/favorites/video/?json=true");
  context.window.setTimeout = (callback) => callback();
  await nextClick;
});

test("pending actions also block matching controls created by fragment replacement", async () => {
  let requests = 0;
  let finishRequest;
  let finishFeedback;
  let signalFeedback;
  const feedbackStarted = new Promise((resolve) => { signalFeedback = resolve; });
  const callbacks = [];
  const context = loadPlaylistContext(() => {
    requests++;
    return new Promise((resolve) => { finishRequest = resolve; });
  }, console, {
    document: { addEventListener: (_event, callback) => callbacks.push(callback) },
    window: {
      setTimeout(callback) {
        finishFeedback = callback;
        signalFeedback();
      },
    },
  });
  const button = new FakeButton({ attributes: { href: "/playlist/add/favorites/video/" } });
  context.preventRefreshButton(button);
  const firstClick = clickButton(button);
  const replacement = new FakeButton({ attributes: { href: "/playlist/remove/favorites/video/" } });
  const event = {
    target: { closest: () => replacement },
    preventDefault() { this.defaultPrevented = true; },
  };
  // Script reloads must preserve the lock while a response is still pending.
  vm.runInContext(source, context);
  await callbacks.at(-1)(event);
  assert.equal(event.defaultPrevented, true);
  assert.equal(requests, 1);
  finishRequest({ ok: true, json: async () => ({ state: "in-playlist" }) });
  await feedbackStarted;
  await callbacks.at(-1)({ ...event, defaultPrevented: false });
  assert.equal(requests, 1);
  finishFeedback();
  await firstClick;
  context.fetch = async () => {
    requests++;
    return { ok: true, json: async () => ({ state: "out-playlist" }) };
  };
  context.window.setTimeout = (callback) => callback();
  await callbacks.at(-1)({ ...event, defaultPrevented: false });
  assert.equal(requests, 2);
});

test("failed actions release their lock immediately without delaying a retry", async () => {
  let requests = 0;
  const errors = [];
  const context = loadPlaylistContext(async () => {
    requests++;
    throw new Error("Network failure");
  }, { error: (...args) => errors.push(args) }, {
    window: { setTimeout() { assert.fail("Failures must not delay a retry"); } },
  });
  const button = new FakeButton({ attributes: { href: "/playlist/add/favorites/video/" } });
  context.preventRefreshButton(button);
  await clickButton(button);
  assert.equal(button.classList.contains("disabled"), false);
  await clickButton(button);
  assert.equal(requests, 2);
  assert.equal(errors.length, 2);
});

for (const config of [
  { status: 403 },
  { status: 500 },
  { response: "<html>Login</html>" },
  { response: JSON.stringify({ error_type: 404, error_text: "Removed video" }) },
]) {
  test("failed player loads preserve the current selection, URL and controls", () => {
    const scenario = createPlayerScenario(false, true, config);
    const previous = scenario.favoriteButton;
    assert.doesNotThrow(() => scenario.context.switchToNextVideo());
    assert.equal(scenario.videos[0].classList.contains("selected"), true);
    assert.equal(scenario.videos[1].classList.contains("selected"), false);
    assert.equal(scenario.favoriteButton, previous);
    assert.equal(scenario.history.length, 0);
    assert.equal(scenario.context.playlistVideoLoading, false);
    assert.equal(scenario.errors.length, 1);
  });
}

test("player transitions remove obsolete management blocks and insert newly allowed blocks", () => {
  const scenario = createPlayerScenario(false, true, {
    initialAside: ["card-manage-video"], aside: { 3: ["card-manage-video"] },
  });
  scenario.context.switchToNextVideo();
  assert.equal(scenario.elements.has("card-manage-video"), false);
  scenario.context.switchToNextVideo();
  assert.equal(scenario.elements.has("card-manage-video"), true);
  assert.deepEqual(scenario.errors, []);
});

test("player transitions skip disabled entries without recursing forever", () => {
  const scenario = createPlayerScenario(false);
  scenario.videos[1].classList.add("disabled");
  scenario.context.switchToNextVideo();
  assert.equal(scenario.videos[2].classList.contains("selected"), true);
  assert.equal(scenario.videoRequests.length, 1);
  scenario.videos.forEach((video) => video.classList.add("disabled"));
  assert.doesNotThrow(() => scenario.context.switchToNextVideo());
  assert.equal(scenario.videoRequests.length, 1);
});

test("chaptered and alternate players use a full navigation to initialize their scripts", () => {
  const scenario = createPlayerScenario(false);
  scenario.videos[1].setAttribute("data-full-page", "true");
  scenario.context.switchToNextVideo();
  assert.equal(scenario.context.window.location.href, scenario.videos[1].getAttribute("href"));
  assert.equal(scenario.videoRequests.length, 0);
});

test("each video transition uses a fresh countdown with the configured duration", async () => {
  const scenario = createPlayerScenario(false);
  const counts = [];
  scenario.context.playlistCount = 3;
  scenario.elements.set("pod-video-countdown", { set textContent(value) { counts.push(value); } });
  await scenario.context.asyncStartCountDown();
  await scenario.context.asyncStartCountDown();
  assert.deepEqual(counts, [3, 2, 1, 3, 2, 1]);
  assert.equal(scenario.context.playlistCount, 3);
});

test("pagination stops after the last page instead of repeatedly requesting it", async () => {
  const scenario = createCardScenario(false);
  const loader = await scenario.loadNextPage();
  assert.equal(loader.nextPage, false);
  await loader.initMore();
  assert.equal(scenario.requests.length, 1);
});

// Execute the real list-refresh code with only its DOM and network boundaries replaced.
function createListRefreshScenario(nextPage) {
  const loaders = [];
  const errors = [];
  let list = { textContent: "" };
  let link = { dataset: { nextpagenumber: "3" }, remove() { link = null; } };
  const newLink = nextPage ? { dataset: { nextpagenumber: "2" } } : null;
  const replacement = { dataset: { nextpage: String(nextPage), countvideos: "12" }, after(value) { link = value; } };
  list.replaceWith = (value) => { list = value; };
  const context = {
    console: { error: (...args) => errors.push(args) }, URLSearchParams,
    fetch: async () => ({ ok: true, text: async () => "fragment" }),
    gettext: (text) => text, ngettext: (one) => one, interpolate: () => "12 videos",
    showLoader() {}, videosListLoader: {},
    document: {
      getElementById: (id) => id === "videos_list" ? list : null,
      querySelector: (selector) => selector === "a.infinite-more-link" ? link : null,
      querySelectorAll: () => [],
    },
    window: { location: { pathname: "/playlist/custom/", search: "" }, history: { pushState() {} } },
    DOMParser: class {
      parseFromString(data) {
        const newList = { ...replacement, marker: data, replaceWith(value) { list = value; } };
        return { body: { querySelector: (selector) => selector === "#videos_list" ? newList : newLink } };
      }
    },
    InfiniteLoader: class {
      constructor(...args) { this.args = args; loaders.push(this); }
      removeLoader() { this.stopped = true; }
    },
  };
  vm.createContext(context);
  const refreshSource = fs.readFileSync(`${__dirname}/../../../../video/static/js/filter_aside_video_list_refresh.js`, "utf8");
  vm.runInContext(refreshSource, context);
  return { context, loaders, errors, get list() { return list; }, get link() { return link; } };
}

for (const nextPage of [false, true]) {
  test("list refresh resets pagination after removals and uses a single query separator", async () => {
    const scenario = createListRefreshScenario(nextPage);
    assert.equal(scenario.context.getUrlForRefresh(), "/playlist/custom/?page=");
    assert.equal(scenario.loaders[0].args[4], 3);
    await scenario.context.refreshVideosSearch();
    assert.equal(scenario.loaders[0].stopped, true);
    assert.equal(scenario.loaders[1].args[3], nextPage);
    assert.equal(scenario.loaders[1].args[4], 2);
    assert.equal(scenario.list.dataset.countvideos, "12");
    assert.equal(Boolean(scenario.link), nextPage);
    assert.deepEqual(scenario.errors, []);
  });
}

for (const failure of [false, true]) {
  test(`an obsolete list refresh cannot overwrite the latest result (failure: ${failure})`, async () => {
    const scenario = createListRefreshScenario(false);
    const responses = [];
    const history = [];
    scenario.context.fetch = () => new Promise((resolve, reject) => responses.push({ resolve, reject }));
    scenario.context.window.history.pushState = (_state, _title, url) => history.push(url);
    scenario.context.window.location.search = "?tag=old";
    const oldRequest = scenario.context.refreshVideosSearch();
    scenario.context.window.location.search = "?tag=new";
    const latestRequest = scenario.context.refreshVideosSearch();
    responses[1].resolve({ ok: true, text: async () => "latest" });
    await latestRequest;
    if (failure) responses[0].reject(new Error("Old request failed"));
    else responses[0].resolve({ ok: true, text: async () => "obsolete" });
    await oldRequest;
    assert.equal(scenario.list.marker, "latest");
    assert.notEqual(scenario.list.textContent, "An Error occurred while processing.");
    assert.deepEqual(history, ["/playlist/custom/?tag=new&page="]);
    assert.equal(scenario.loaders.length, 2);
  });
}

test("finishing an obsolete request leaves the current loading indicator active", async () => {
  const scenario = createListRefreshScenario(false);
  const responses = [];
  const loading = [];
  scenario.context.fetch = () => new Promise((resolve) => responses.push(resolve));
  scenario.context.showLoader = (_element, state) => loading.push(state);
  const oldRequest = scenario.context.refreshVideosSearch();
  const latestRequest = scenario.context.refreshVideosSearch();
  responses[0]({ ok: true, text: async () => "obsolete" });
  await oldRequest;
  assert.equal(loading.at(-1), true);
  responses[1]({ ok: true, text: async () => "latest" });
  await latestRequest;
  assert.equal(loading.at(-1), false);
});

test("stopping pagination also ignores its in-flight response", async () => {
  let finishRequest;
  let afterLoads = 0;
  const list = { innerHTML: "reordered cards" };
  const context = {
    console, fetch: () => new Promise((resolve) => { finishRequest = resolve; }),
    window: { addEventListener() {}, removeEventListener() {} },
    document: { querySelector: () => ({}), getElementById: () => list },
    DOMParser: class { parseFromString() { assert.fail("A stopped loader must not parse or append its response"); } },
  };
  vm.createContext(context);
  const source = fs.readFileSync(`${__dirname}/../../../../main/static/js/infinite.js`, "utf8");
  vm.runInContext(`${source}; this.InfiniteLoader = InfiniteLoader;`, context);
  const loader = new context.InfiniteLoader("/playlist/custom/?page=", () => {}, () => { afterLoads++; });
  const pending = loader.initMore();
  await loader.initMore();
  loader.removeLoader();
  assert.equal(afterLoads, 1);
  loader.removeLoader();
  finishRequest({ ok: true, text: async () => "old page" });
  await pending;
  assert.equal(list.innerHTML, "reordered cards");
  assert.equal(afterLoads, 1);
});

test("playlist editing works when promotion is disabled or not permitted", () => {
  const visibility = new FakeButton();
  visibility.value = "private";
  const password = new FakeButton();
  const passwordGroup = new FakeButton();
  password.closest = () => passwordGroup;
  const elements = {
    id_visibility: visibility, id_password: password,
    id_visibilityHelp: { parentNode: { insertBefore() {} } },
  };
  const context = { gettext: (text) => text, document: {
    getElementById: (id) => elements[id] || null,
    createElement: () => new FakeButton(),
  } };
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(`${__dirname}/add-or-edit.js`, "utf8"), context);
  for (const value of ["protected", "public", "private"]) {
    visibility.listeners.get("change")({ target: { value } });
    assert.equal(password.required, value === "protected");
    assert.equal(passwordGroup.classList.contains("d-none"), value !== "protected");
  }
});
