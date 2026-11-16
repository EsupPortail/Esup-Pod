/**
 * @file Esup-Pod delegated playlist and favorite card removal.
 */

/* global bootstrap, postPlaylistAction, reportPlaylistError, refreshVideosSearch */

// Delegate clicks so pagination and filtering can replace cards without rebinding.
document.addEventListener("click", async function (event) {
  const button = event.target.closest("#videos_list [data-remove-playlist-card]");
  if (!button) return;
  event.preventDefault();
  if (button.classList.contains("disabled")) return;
  button.classList.add("disabled");
  try {
    const data = await postPlaylistAction(button);
    if (data.state !== "out-playlist") throw new Error("Unexpected removal state");
    const tooltip = bootstrap.Tooltip.getInstance(button);
    if (tooltip) tooltip.dispose();
    button.closest(".draggable-container").remove();
    // Deletion shifts page boundaries; reload the filtered list and its pagination.
    refreshVideosSearch();
  } catch (error) {
    reportPlaylistError(error);
  } finally {
    button.classList.remove("disabled");
  }
});
