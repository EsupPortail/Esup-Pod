/**
 * @file Esup-Pod link video modal functions
 * @since 3.7.1
 */

/* Read-only Globals defined in utils-playlist.js */
/*
global preventRefreshButton
*/

/**
 * Add event listener for the playlist modal in video page.
 */
function addEventListenerForModal() {
  const playlists = document.getElementById("playlist-list").children;
  const buttons = [];
  for (let playlist of playlists) {
    buttons.push(playlist.querySelector(".action-btn"));
  }

  for (let button of buttons) {
    preventRefreshButton(button, false);
  }
}

document.addEventListener('DOMContentLoaded', function () {
  addEventListenerForModal();
});
