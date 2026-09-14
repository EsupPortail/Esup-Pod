/**
 * @file Esup-Pod playlist card removal.
 */

/* global postPlaylistAction */

document.addEventListener("DOMContentLoaded", function () {
  const cards = document.getElementsByClassName("draggable-container");
  for (let card of cards) {
    const btn = card.querySelector(".remove-from-playlist-btn-link");
    if (!btn) continue;
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      return postPlaylistAction(btn)
        .then((response) => {
          if (response.ok) {
            return response.text();
          } else {
            throw new Error("Network response was not ok.");
          }
        })
        .then((data) => {
          card.remove();
          const parser = new DOMParser();
          const html = parser.parseFromString(data, "text/html");
          const title = document.getElementById("video_count");
          title.replaceWith(html.getElementById("video_count"));
        })
        .catch((error) => {
          console.error("Error: ", error);
        });
    });
  }
});
