document.addEventListener("DOMContentLoaded", function () {
  const playlists = document.getElementById("playlist-list").children;
  const buttons = [];
  for (let playlist of playlists) {
    buttons.push(playlist.querySelector(".action-btn"));
  }

  for (let button of buttons) {
    preventRefreshButton(button);
  }
});
