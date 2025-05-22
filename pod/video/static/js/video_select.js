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
// var resetDashboardElementsBtn = document.getElementById(
//   "reset-dashboard-elements-btn",
// );
var countSelectedVideosBadge = document.getElementById(
  "countSelectedVideosBadge",
);

document.addEventListener("DOMContentLoaded", () => {
  toggleBulkUpdateVisibility();
  selectAllManger();
});

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
  const applyMultipleActionsBtn = document.getElementById("applyBulkUpdateBtn");
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
  // manageDisableBtn(resetDashboardElementsBtn, newCount > 0);
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
  toggleBulkUpdateVisibility(container);
  if (container === videosListContainerId) {
    replaceSelectedCountVideos(container);
  }
}

/**
 * Toggles the bulk update UI visibility based on video selection and total count.
 *
 * Shows the container and related elements if videos are selected and count > 0.
 * Otherwise, hides the container and restores default display.
 */
function toggleBulkUpdateVisibility(container) {
  try {
    const c = document.getElementById('bulk-update-container');
    const hr = document.getElementById('bottom-ht-filtre');
    const skipLink = document.getElementById('skipToBulk');
    const countVideos = parseInt(document.getElementById("videos_list")?.dataset.countvideos || "0", 10);
    const hasSelection = hasSelectedVideos();

    let shouldShow = false;
    if(container) shouldShow = hasSelection && countVideos > 0 && container === 'videos_list';
    else shouldShow = hasSelection && countVideos > 0;

    if (!c || !hr || !skipLink) {
      throw new Error(JSON.stringify({
        reason: 'Missing DOM element(s)',
        elements: {
          'bulk-update-container': c === null ? 'NOT FOUND' : 'OK',
          'bottom-ht-filtre': hr === null ? 'NOT FOUND' : 'OK',
          'skipToBulk': skipLink === null ? 'NOT FOUND' : 'OK'
        }
      }));
    }

    if (shouldShow) {
      hr.style.display = 'none';
      c.classList.add('visible');
      skipLink.classList.add('is-visible');
    } else {
      hr.style.display = 'block';
      c.classList.remove('visible');
      skipLink.classList.remove('is-visible');
    }

  } catch (error) {
    console.error(`Error in video_select.js (toggleBulkUpdateVisibility function). Failed to toggle bulk update UI because ${error.message}`);
  }
}


/**
 * Checks whether at least one video has been selected.
 *
 * @returns {boolean} `true` if any entry in `selectedVideos` contains one or more videos, otherwise `false`.
 */
function hasSelectedVideos() {
  try {
    return Object.values(selectedVideos).some(arr => Array.isArray(arr) && arr.length > 0);
  } catch (error) {
    console.error(`Error in video_select.js (hasSelectedVideos function). Failed to check video selection because ${error.message}`);
    return false;
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
  try {
    const checkbox = document.getElementById('selectAll');

    if (!checkbox) {
      throw new Error('Checkbox with id "selectAll" not found in DOM');
    }
    checkbox.checked = false;
    clearSelectedVideo(videosListContainerId);
    toggleBulkUpdateVisibility();
    dashboardActionReset();
    window.scrollTo(0, 0);
  } catch (error) {
    console.error(`Error in video_select.js (resetDashboardElements function). Failed to reset dashboard elements because ${error.message}`);
  }
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
  try {
    if (typeof container !== 'string' || container.trim() === '') throw new Error('Invalid container identifier provided');

    const selector = "#" + container + " .card-select-input";
    const elements = document.querySelectorAll(selector);
    if (elements.length > 1) {
      elements.forEach((elt) => {
        elt.checked = true;
      });
      setListSelectedVideos(container);
      toggleBulkUpdateVisibility(container);
      replaceSelectedCountVideos(container);
    }
  } catch (error) {
    console.error(`Error in video_select.js (selectAllVideos function). Failed to select all videos because ${error.message}`);
  }
}


/**
 * Sets up the "Select All" checkbox behavior for managing video selection.
 */
function selectAllManger() {
  try {
    const checkbox = document.getElementById('selectAll');
    if (checkbox) {
      checkbox.addEventListener('change', () => {
        try {
          if (checkbox.checked) {
            selectAllVideos(videosListContainerId);
          } else {
            resetDashboardElements();
          }
        } catch (innerError) {
          console.error(`Error in video_select.js (selectAllManger > change event). Failed to process checkbox change because ${innerError.message}`);
        }
      });
    }
  } catch (error) {
    console.error(`Error in video_select.js (selectAllManger function). Failed to initialize "Select All" behavior because ${error.message}`);
  }
}

