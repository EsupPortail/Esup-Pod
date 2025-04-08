/**
 * @file Esup-Pod functions for video selection manage.
 * @since 3.5.0
 */

// Read-only globals defined in dashboard.js
/*
  global dashboardActionReset
*/

/* exported resetDashboardElements getHTMLBadgesSelectedTitles toggleSelectedVideo setSelectedVideos */

var selectedVideos = {};
var applyMultipleActionsBtn = document.getElementById("applyBulkUpdateBtn");
var resetDashboardElementsBtn = document.getElementById(
  "reset-dashboard-elements-btn",
);
var countSelectedVideosBadge = document.getElementById(
  "countSelectedVideosBadge",
);

/**
 * Get list of selected videos's titles based on selected videos
 *
 * @param {string} container - Identifier of container = selectedVideos's key
 * @returns {*[video_title]}
 */
function getListSelectedVideosTitles(container) {
  let selectedTitles = [];
  if (selectedVideos[container].length > 0) {
    Array.from(selectedVideos[container]).forEach((v) => {
      let item = document.querySelector(
        "#" + container + " .infinite-item[data-slug='" + v + "']",
      );
      selectedTitles.push(
        item.querySelector(".dashboard-video-title").dataset.videoTitle,
      );
    });
  }
  return selectedTitles;
}

/**
 * Set shared/global variable selectedVideos with selected videos based on class selected
 *
 * @param {string} container - Identifier of container = selectedVideos's key
 */
function setListSelectedVideos(container) {
  if (container === videosListContainerId) {
    selectedVideos[container] = [];
  }
  let selector = "#" + container + " .card-select-input:checked";
  document.querySelectorAll(selector).forEach((elt) => {
    if (selectedVideos[container].indexOf(elt.dataset.slug) === -1) {
      selectedVideos[container].push(elt.dataset.slug);
    }
  });
}

/**
 * Set directly selected videos on interface to improve user experience
 *
 * @param {string} container - Identifier of container = selectedVideos's key
 */
function setSelectedVideos(container) {
  Array.from(selectedVideos[container]).forEach((elt) => {
    let selector =
      "#" + container + ' .card-select-input[data-slug="' + elt + '"]';
    let domElt = document.querySelector(selector);
    if (domElt && !domElt.checked) {
      domElt.checked = true;
    }
  });
}

/**
 * Replace count of selected videos (count label in "Apply" bulk update's badge)
 *
 * @param {string} container - Identifier of container = selectedVideos's key
 */
function replaceSelectedCountVideos(container) {
  let newCount = selectedVideos[container].length;
  let videoCountStr = ngettext("%(count)s video", "%(count)s videos", newCount);
  let videoCountTit = ngettext(
    "%(count)s video selected",
    "%(count)s videos selected",
    newCount,
  );
  videoCountStr = interpolate(videoCountStr, { count: newCount }, true);
  countSelectedVideosBadge.textContent = videoCountStr;
  countSelectedVideosBadge.setAttribute("title", videoCountTit);
  manageDisableBtn(
    applyMultipleActionsBtn,
    newCount > 0 && dashboardAction.length !== 0,
  );
  manageDisableBtn(resetDashboardElementsBtn, newCount > 0);
}

/**
 * Toggle class selected for video cards or list-item, avoid select a video when click on links
 *
 * @param {HTMLElement} item - HTMLElement to be toggled
 * @param {string} container - Identifier of container = selectedVideos's key
 */
function toggleSelectedVideo(item, container) {
  if (item.checked) {
    if (!selectedVideos[container].includes(item.dataset.slug)) {
      selectedVideos[container].push(item.dataset.slug);
    }
  } else {
    if (selectedVideos[container].includes(item.dataset.slug)) {
      selectedVideos[container].splice(
        selectedVideos[container].indexOf(item.dataset.slug),
        1,
      );
    }
  }
  if (container === videosListContainerId) {
    replaceSelectedCountVideos(container);
  }
}

/**
 * Clear videos selection: deselect all videos, reset badge count
 *
 * @param {string} container - Identifier of container = selectedVideos's key
 */
function clearSelectedVideo(container) {
  selectedVideos[container] = [];
  document.querySelectorAll(".card-select-input").forEach((elt) => {
    elt.checked = false;
  });
  replaceSelectedCountVideos(container);
}

/**
 * Reset dashboard elements (selected videos, action)
 * @see dashboardActionReset
 * @see resetDashboardElementsBtn
 **/
function resetDashboardElements() {
  clearSelectedVideo(videosListContainerId);
  dashboardActionReset();
  window.scrollTo(0, 0);
}

/**
 * Get list of selected videos slugs (HTML li formated) for modal confirm display.
 *
 * @param {HTMLElement} container - The container element that holds the selected videos.
 * @returns {string} HTML string of badges for the selected video titles.
 */
function getHTMLBadgesSelectedTitles(container) {
  let str = "";
  Array.from(getListSelectedVideosTitles(container)).forEach((title) => {
    str +=
      "<span class='badge rounded-pill bulk-update-confirm-badges'>" +
      title +
      "</span>";
  });
  return str;
}

/**
 * Select all videos (visible infinite-item) on given container
 *
 * @param {string} container - Identifier of the infinite-items's container
 */
function selectAllVideos(container) {
  let selector = "#" + container + " .card-select-input";
  document.querySelectorAll(selector).forEach((elt) => {
    elt.checked = true;
  });
  setListSelectedVideos(container);
  replaceSelectedCountVideos(container);
}
