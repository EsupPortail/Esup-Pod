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
 * Get list of selected videos's titles based on class selected
 * @returns {*[video_title]}
 */
function getListSelectedVideosTitles(container) {
  let selectedTitles = [];
  if (selectedVideos[container].length > 0) {
    Array.from(selectedVideos[container]).forEach((v) => {
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
function setListSelectedVideos(container) {
  if(container === videosListContainerId){
    selectedVideos[container] = [];
  }
  let selector = "#" + container + " .infinite-item.selected";
  document.querySelectorAll(selector).forEach((elt) => {
    if(selectedVideos[container].indexOf(elt.dataset.slug) === -1){
      selectedVideos[container].push(elt.dataset.slug);
    }
  });
}

/**
 * Set directly selected videos on interface to improve user experience
 */
function setSelectedVideos(container) {
  Array.from(selectedVideos[container]).forEach((elt) => {
    let selector = '#' + container + ' .infinite-item[data-slug="' + elt + '"]';
    let domElt = document.querySelector(selector);
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
}

/**
 * Toggle class selected for video cards or list-item, avoid select a video when click on links
 * @param item
 */
function toggleSelectedVideo(item, container) {
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
  if(item.classList.contains("selected")){
    if(!selectedVideos[container].includes(item.dataset.slug)){
      selectedVideos[container].push(item.dataset.slug);
    }
  }else{
    if (selectedVideos[container].includes(item.dataset.slug)){
      selectedVideos[container].splice(selectedVideos[container].indexOf(item.dataset.slug),1);
    }
  }
  //setListSelectedVideos(container);
  if(container === "videos_list") {
    replaceSelectedCountVideos(container);
  }
}

/**
 * Clear videos selection : deselect all videos, reset badge count
 */
function clearSelectedVideo(container) {
  selectedVideos[container] = [];
  document.querySelectorAll(".infinite-item.selected").forEach((elt) => {
    elt.classList.remove("selected");
  });
  replaceSelectedCountVideos(container);
}

/**
 * Reset dashboard elements (selected videos, action)
 * @see dashboardActionReset
 * @see resetDashboardElementsBtn
 **/
function resetDashboardElements() {
  clearSelectedVideo();
  dashboardActionReset();
  window.scrollTo(0, 0);
}

/**
 * Get list of selected videos slugs (HTML li formated) for modal confirm display
 */
function getHTMLBadgesSelectedTitles() {
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
 * @param {string} container : Identifier of the infinite-items's container
 */
function selectAllVideos(container){
  let selector = "#" + container + " .infinite-item";
  document.querySelectorAll(selector).forEach((elt) => {
    elt.classList.add("selected");
  });
  setListSelectedVideos(container);
  replaceSelectedCountVideos(container);
}
