/**
 * @file Esup-Pod delegated playlist and favorite card removal.
 */

/* global postPlaylistAction */

// Delegate clicks so pagination and filtering can replace cards without rebinding.
document.addEventListener("click", function (event) {
  const button = event.target.closest("#videos_list [data-remove-playlist-card]");
  if (!button) return;
  event.preventDefault();
  if (button.classList.contains("disabled")) return;
  button.classList.add("disabled");
  return postPlaylistAction(button)
    .then((response) => {
      if (!response.ok) throw new Error(gettext("Network response was not ok."));
      return response.text();
    })
    .then((data) => {
      const html = new DOMParser().parseFromString(data, "text/html");
      button.closest(".draggable-container").remove();
      document.getElementById("video_count").replaceWith(html.getElementById("video_count"));
    })
    .catch((error) => {
      console.error("Error: ", error);
    })
    .finally(() => {
      button.classList.remove("disabled");
    });
});
