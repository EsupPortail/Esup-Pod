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
      let url = this.getAttribute("href");
      if (button.classList.contains("action-btn")) {
        button.classList.add("disabled");
        this.removeAttribute("href");
      } else if (button.classList.contains("favorite-btn-link")) {
        button.classList.add("disabled");
      }
      if (jsonFormat && !url.includes("json=true")) {
        url += `${url.includes("?") ? "&" : "?"}json=true`;
      }
      fetch(url, {
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
            window.setTimeout(() => {
              const iconElement = button.querySelector(".bi");
              const isInPlaylist = data.state === "in-playlist";
              const newUrl = isInPlaylist
                ? url.replace("/add/", "/remove/")
                : url.replace("/remove/", "/add/");
              const oldIcon = isInPlaylist ? "bi-plus" : "bi-dash";
              const newIcon = isInPlaylist ? "bi-dash" : "bi-plus";
              const oldButtonClass = isInPlaylist
                ? "btn-success"
                : "btn-danger";
              const newButtonClass = isInPlaylist
                ? "btn-danger"
                : "btn-success";
              const oldActionClass = isInPlaylist
                ? "add-video-from-playlist"
                : "remove-video-from-playlist";
              const newActionClass = isInPlaylist
                ? "remove-video-from-playlist"
                : "add-video-from-playlist";
              const actionLabel = isInPlaylist
                ? gettext("Remove the video from this playlist")
                : gettext("Add the video in this playlist");

              if (data.state !== "in-playlist" && data.state !== "out-playlist") {
                return;
              }
              iconElement.classList.remove(oldIcon);
              iconElement.classList.add(newIcon);
              button.classList.remove(oldButtonClass, oldActionClass, "disabled");
              button.classList.add(newButtonClass, newActionClass);
              button.setAttribute("href", newUrl);
              button.setAttribute("title", actionLabel);
              button.setAttribute("aria-label", actionLabel);
            }, 300);
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
          // Hide empty menu and change style for favorite button
          // hideEmptyDropdowns();
        })
        .catch((error) => {
          console.error("Error: ", error);
        });
    });
  }
}
