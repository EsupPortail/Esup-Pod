/**
 * @file Esup-pod Playlist utils.
 * @since 3.4.0
 */

/**
 * Submit a playlist mutation without following redirects to login or error pages.
 * @param {HTMLElement} button - The control carrying the rendered CSRF token.
 * @returns {Promise<Object>} The validated membership response.
 */
async function postPlaylistAction(button) {
  const url = button.getAttribute("href");
  const response = await fetch(`${url}${url.includes("?") ? "&" : "?"}json=true`, {
    method: "POST",
    mode: "same-origin",
    redirect: "error",
    headers: { "X-CSRFToken": button.getAttribute("data-csrf-token") },
  });
  if (!response.ok || response.redirected) throw new Error("Playlist request failed");
  const data = await response.json();
  if (!["in-playlist", "out-playlist"].includes(data.state)) {
    throw new Error("Unexpected playlist state");
  }
  return data;
}

/**
 * Report a failed action without changing the displayed membership state.
 * @param {Error} error - The request or response error.
 */
function reportPlaylistError(error) {
  console.error("Playlist action failed:", error);
  if (typeof showalert === "function") {
    showalert(gettext("An Error occurred while processing."), "alert-danger");
  }
}

/**
 * Apply a successful mutation and restore the control after failures.
 * @param {Event} event - The click on a favorite or modal control.
 */
async function handlePlaylistAction(event) {
  event.preventDefault();
  const url = this.getAttribute("href");
  const action = url?.replace("/remove/", "/add/");
  if (!url || this.classList.contains("disabled") || playlistPendingActions.has(action)) return;
  playlistPendingActions.add(action);
  this.classList.add("disabled");
  try {
    const data = await postPlaylistAction(this);
    updatePlaylistButton(this, data.state, url);
    const playlistId = this.getAttribute("data-playlist-id");
    const videoId = this.getAttribute("data-video-id");
    if (playlistId && videoId) {
      document.querySelectorAll(`[data-playlist-id="${playlistId}"][data-video-id="${videoId}"]`).forEach((button) => {
        if (button !== this) updatePlaylistButton(button, data.state, button.getAttribute("href"));
      });
    }
    // Keep successful feedback visible and ignore rapid clicks on matching controls.
    await new Promise((resolve) => window.setTimeout(resolve, 300));
    if (data.state === "out-playlist" && this.getAttribute("data-removed-url")) {
      window.location.href = this.getAttribute("data-removed-url");
    }
  } catch (error) {
    reportPlaylistError(error);
  } finally {
    this.classList.remove("disabled");
    playlistPendingActions.delete(action);
  }
}

var playlistBoundButtons = playlistBoundButtons || new WeakSet();
var playlistPendingActions = playlistPendingActions || new Set();

/**
 * Keep existing callers compatible while making repeated binding harmless.
 * @param {HTMLElement} button - A control from the initial or a replaced fragment.
 */
function preventRefreshButton(button) {
  if (button && button.getAttribute("data-remove-playlist-card") === null && !playlistBoundButtons.has(button)) {
    playlistBoundButtons.add(button);
    button.addEventListener("click", handlePlaylistAction);
  }
}

// Filtering and modal replacement can create controls without running their scripts.
document.addEventListener("click", function (event) {
  if (event.defaultPrevented) return;
  const button = event.target.closest(".favorite-btn-link, #favorite-button, #playlist-list .action-btn");
  if (button && button.getAttribute("data-remove-playlist-card") === null) {
    return handlePlaylistAction.call(button, event);
  }
});

/**
 * Update a modal button or a favorite star after a successful JSON response.
 * @param {HTMLElement} button - The action button.
 * @param {string} state - The new playlist membership state.
 * @param {string} url - The URL used for the action.
 */
function updatePlaylistButton(button, state, url) {
  if (state !== "in-playlist" && state !== "out-playlist") {
    throw new Error("Unexpected playlist state");
  }
  const isInPlaylist = state === "in-playlist";
  const isFavorite = button.id === "favorite-button" || button.classList.contains("favorite-btn-link");
  const icons = isFavorite ? ["bi-star", "bi-star-fill"] : ["bi-plus", "bi-dash"];
  const icon = button.querySelector(".bi");
  icon?.classList.remove(...icons);
  icon?.classList.add(icons[Number(isInPlaylist)]);

  let label;
  if (isFavorite) {
    label = isInPlaylist ? gettext("Remove from favorite") : gettext("Add in favorite");
    button.setAttribute("aria-pressed", String(isInPlaylist));
  } else {
    label = isInPlaylist
      ? gettext("Remove the video from this playlist")
      : gettext("Add the video in this playlist");
    button.classList.remove(
      "btn-success", "btn-danger", "add-video-from-playlist", "remove-video-from-playlist",
    );
    button.classList.add(
      isInPlaylist ? "btn-danger" : "btn-success",
      isInPlaylist ? "remove-video-from-playlist" : "add-video-from-playlist",
    );
  }
  button.setAttribute("href", isInPlaylist
    ? url.replace("/add/", "/remove/")
    : url.replace("/remove/", "/add/"));
  button.setAttribute("title", label);
  button.setAttribute("aria-label", label);
}
