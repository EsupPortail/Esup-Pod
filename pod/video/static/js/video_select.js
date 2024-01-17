/**
 * @file Esup-Pod functions for video selection manage.
 * @since 3.5.0
 */
var selectedVideos = [];
var applyMultipleActionsBtn = document.getElementById("applyBulkUpdateBtn");
var resetSelectedVideosBtn = document.getElementById("resetSelectedVideosBtn");
var countSelectedVideosBadge = document.getElementById(
  "countSelectedVideosBadge",
);

/**
 * Get list of selected videos's titles based on class selected
 * @returns {*[video_title]}
 */
function getListSelectedVideosTitles() {
  let selectedTitles = [];
  if (selectedVideos.length > 0) {
    Array.from(selectedVideos).forEach((v) => {
      let item = document.querySelector(
        ".infinite-item.selected[data-slug='" + v + "']",
      );
      selectedTitles.push(
        item.querySelector(".dashboard-video-title").getAttribute("title"),
      );
    });
  }
  return selectedTitles;
}

/**
 * Set shared/global variable selectedVideos with selected videos based on class selected
 */
function setListSelectedVideos() {
  selectedVideos = [];
  document.querySelectorAll(".infinite-item.selected").forEach((elt) => {
    selectedVideos.push(elt.dataset.slug);
  });
}

/**
 * Set directly selected videos on interface to improve user experience
 */
function setSelectedVideos() {
  Array.from(selectedVideos).forEach((elt) => {
    let domElt = document.querySelector(
      '#videos_list .infinite-item[data-slug="' + elt + '"]',
    );
    if (domElt && !domElt.classList.contains("selected")) {
      if (!domElt.classList.contains("selected")) {
        domElt.classList.add("selected");
      }
    }
  });
}

/**
 * Replace count of selected videos (count label in "Apply" bulk update's badge)
 */
function replaceSelectedCountVideos() {
  let newCount = selectedVideos.length;
  let videoCountStr = ngettext(`%(count)s video`, `%(count)s videos`, newCount);
  videoCountStr = interpolate(videoCountStr, { count: newCount }, true);
  countSelectedVideosBadge.innerHTML = videoCountStr;
  countSelectedVideosBadge.setAttribute("title", videoCountStr);
  manageDisableBtn(
    applyMultipleActionsBtn,
    newCount > 0 && action.length !== 0,
  );
  manageDisableBtn(resetSelectedVideosBtn, newCount > 0);
}

/**
 * Toggle class selected for video cards or list-item, avoid select a video when click on links
 * @param item
 */
function toggleSelectedVideo(item) {
  // Prevent item to select if link is clicked
  if (
    event.target.tagName === "A" ||
    event.target.tagName === "BUTTON" ||
    event.target.classList.contains("card-footer-link-i") ||
    event.target.classList.contains("more-actions-row-i") ||
    (event.keyCode && event.keyCode !== 13)
  ) {
    return;
  }
  item.classList.toggle("selected");
  setListSelectedVideos();
  replaceSelectedCountVideos();
}

/**
 * Clear videos selection : deselect all videos, reset badge count
 */
function clearSelectedVideo() {
  selectedVideos = [];
  document.querySelectorAll(".infinite-item.selected").forEach((elt) => {
    elt.classList.remove("selected");
  });
  replaceSelectedCountVideos();
}

/**
 * Get list of selected videos slugs (HTML li formated) for modal confirm display
 */
function getHTMLBadgesSelectedTitles() {
  let str = "";
  Array.from(getListSelectedVideosTitles()).forEach((title) => {
    str +=
      "<span class='badge rounded-pill bulk-update-confirm-badges'>" +
      title +
      "</span>";
  });
  return str;
}
