/**
 * @file Esup-pod Playlist utils.
 * @since 3.4.0
 */

/* Read-only Globals defined in playlist-modal.js */
/*
global addEventListenerForModal
*/

/**
 * Disables the default refresh behavior of a button and performs an asynchronous GET request using the Fetch API.
 * @param {HTMLElement} button - The HTML button element.
 */
function preventRefreshButton(button, jsonFormat) {
  const FAVORITE_BUTTON_ID = "favorite-button";
  const PLAYLIST_MODAL_ID = "playlist-list";
  if (button) {
    button.addEventListener("click", function (e) {
      e.preventDefault();
      const originalUrl = this.getAttribute("href");
      if (!originalUrl || button.classList.contains("disabled")) return;
      let url = originalUrl;
      if (button.classList.contains("action-btn")) {
        button.classList.add("disabled");
        this.removeAttribute("href");
      } else if (button.classList.contains("favorite-btn-link")) {
        button.classList.add("disabled");
      }
      if (jsonFormat && !url.includes("json=true")) {
        url += `${url.includes("?") ? "&" : "?"}json=true`;
      }
      return fetch(url, {
        method: "GET",
      })
        .then((response) => {
          if (response.ok) {
            if (jsonFormat) {
              return response.json();
            }
            return response.text();
          } else {
            throw new Error("Network response was not ok.");
          }
        })
        .then((data) => {
          if (jsonFormat) {
            updatePlaylistButton(button, data.state, url);
          } else {
            const parser = new DOMParser();
            const html = parser.parseFromString(data, "text/html");
            const updatedButton = html.getElementById(button.id);
            const favoriteButton = document.getElementById(FAVORITE_BUTTON_ID);
            const playlistModal = document.getElementById(PLAYLIST_MODAL_ID);
            preventRefreshButton(updatedButton);
            button.replaceWith(updatedButton);
            if (playlistModal && button.id === FAVORITE_BUTTON_ID) {
              playlistModal.replaceWith(html.getElementById(PLAYLIST_MODAL_ID));
              addEventListenerForModal();
            }
            if (favoriteButton && button.id !== FAVORITE_BUTTON_ID) {
              const updatedFavoriteButton =
                html.getElementById(FAVORITE_BUTTON_ID);
              preventRefreshButton(updatedFavoriteButton, false);
              favoriteButton.replaceWith(updatedFavoriteButton);
            }
          }
        })
        .catch((error) => {
          console.error("Error: ", error);
        })
        .finally(() => {
          button.classList.remove("disabled");
          if (!button.getAttribute("href")) button.setAttribute("href", originalUrl);
        });
    });
  }
}

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
  const isFavorite = button.classList.contains("favorite-btn-link");
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
