/**
 * @file Esup-Pod functions for the playlist player.
 * @since 3.5.0
 */

/* exported asyncStartCountDown, handlePlaylistVideoEnded */

// Globals defined in playlist_player.html and utils-playlist.js
/*
  global playlistCount, preventRefreshButton, reportPlaylistError
*/


/**
 * This variable is `true` if the enrichment is active for the current page.
 */
var enrichmentIsOn = false;
var playlistVideoLoading = false;

/**
 * Link for the stylesheet for the enrichment application.
 */
var linkForStyleSheetForEnrichment;

/**
 * Advance after the countdown without disposing a player whose next request may fail.
 */
async function handlePlaylistVideoEnded() {
  const endedPlayer = player;
  if (playlistCount >= 3) {
    document.querySelector('.vjs-big-play-button')?.remove();
    await asyncStartCountDown();
  }
  if (player === endedPlayer) switchToNextVideo();
}

/**
 * Switch to the next video when this exists.
 * (Used in video-script.html)
 */
function switchToNextVideo() {
  const playerElements = Array.from(document.querySelectorAll('.player-element'));
  const selectedElement = document.querySelector('.selected');
  const currentIndex = playerElements.indexOf(selectedElement);
  if (!selectedElement || !playerElements.length || playlistVideoLoading) return;
  const nextElement = playerElements.slice(currentIndex + 1)
    .concat(playerElements.slice(0, currentIndex + 1))
    .find((element) => !element.classList.contains('disabled'));
  if (!nextElement) return;
  const videoUrl = nextElement.getAttribute('href');
  if (nextElement.getAttribute('data-full-page') !== null || selectedElement.getAttribute('data-full-page') !== null) {
    window.location.href = videoUrl;
    return;
  }
  playlistVideoLoading = true;
  const xhr = new XMLHttpRequest();
  xhr.open('GET', nextElement.getAttribute('data-url-for-video'));
  xhr.timeout = 30000;
  xhr.onreadystatechange = function () {
    if (xhr.readyState !== 4) return;
    let renderingStarted = false;
    try {
      if (xhr.status !== 200) throw new Error(`Playlist video request failed: ${xhr.status}`);
      const data = JSON.parse(xhr.responseText);
      if (data.error_type || !data.page_content || !data.page_aside) {
        throw new Error("Invalid playlist video response");
      }
      renderingStarted = true;
      replacePlaylistVideo(data, nextElement);
    } catch (error) {
      reportPlaylistError(error);
      // A partial DOM replacement must recover through the complete player view.
      if (renderingStarted) window.location.href = videoUrl;
    } finally {
      playlistVideoLoading = false;
      scrollToSelectedVideo();
    }
  };
  xhr.send();
}

/**
 * Replace validated player fragments and initialize the current video's controls.
 * @param {Object} responseData - The authorized fragments returned by the server.
 * @param {HTMLElement} nextElement - The playlist entry being loaded.
 */
function replacePlaylistVideo(responseData, nextElement) {
  const parser = new DOMParser();
  const opengraphHtml = parser.parseFromString(responseData.opengraph, 'text/html');
  const breadcrumbs = parser.parseFromString(responseData.breadcrumbs, 'text/html');
  const pageAside = parser.parseFromString(responseData.page_aside, 'text/html');
  const pageContent = parser.parseFromString(responseData.page_content, 'text/html');
  const moreScript = parser.parseFromString(responseData.more_script, 'text/html');
  const pageTitle = parser.parseFromString(responseData.page_title, 'text/html');
  enrichmentIsOn = responseData.enrichment_is_on;
  if (!pageContent.querySelector('#video-player') || !moreScript.querySelector('#more-script')) {
    throw new Error("Incomplete playlist video response");
  }
  if (typeof player !== 'undefined' && typeof player.dispose === 'function') player.dispose();

  const coupleOfElements = [
    ['meta', 'property', 'head'],
    ['meta', 'name', 'head'],
  ];
  for (let coupleOfElement of coupleOfElements) {
    const metaTags = opengraphHtml.querySelectorAll(`${coupleOfElement[0]}[${coupleOfElement[1]}]`);
    metaTags.forEach(metaTag => {
      const elementToRefresh = document.querySelector(`${coupleOfElement[0]}[${coupleOfElement[1]}="${metaTag.getAttribute(coupleOfElement[1])}"]`);
      if (elementToRefresh) {
        document.querySelector(`${coupleOfElement[0]}[${coupleOfElement[1]}="${metaTag.getAttribute(coupleOfElement[1])}"]`).setAttribute('content', metaTag.getAttribute('content'));
      } else {
        document.querySelector(coupleOfElement[2]).appendChild(metaTag);
      }
    });
  }
  refreshElementWithDocumentFragment('#mainbreadcrumb', breadcrumbs);
  const idElements = [
    'card-manage-video',
    'card-takenote',
    'card-share',
    'card-disciplines',
    'card-types',
    'card-manage-quiz',
    'card-enrichment-informations',
  ];
  for (let id of idElements) {
    refreshElementWithDocumentFragment(`#${id}`, pageAside, true);
  }

  refreshElementWithDocumentFragment('#video-player', pageContent);
  if (typeof preventRefreshButton === 'function') {
    preventRefreshButton(document.getElementById('favorite-button'));
    document.querySelectorAll('#playlist-list .action-btn').forEach((button) => {
      preventRefreshButton(button, true);
    });
  }
  countdownElement = document.getElementById('pod-video-countdown');
  refreshElementWithDocumentFragment('#more-script', moreScript);
  refreshElementWithDocumentFragment('title', pageTitle);
  const selectedElement = document.querySelector('.selected');
  selectedElement.classList.remove('selected');
  selectedElement.querySelector('span.rank').textContent = selectedElement.id;
  nextElement.classList.add('selected');
  nextElement.querySelector('span.rank').innerHTML = '<i class="bi bi-caret-right-fill" aria-hidden="true"></i>';
  updateUrl(nextElement.getAttribute('href'));
  document.querySelectorAll('script').forEach((item) => {
    if (item.id == 'id_video_script') (0, eval)(item.innerHTML);
    if (item.id == 'id_video_enrichment_script') (0, eval)(item.innerHTML);
  });
  let styleElementForEnrichment = document.getElementById('enrichment_style_id');
  if (enrichmentIsOn) {
    if (!styleElementForEnrichment) {
      let styleElementForEnrichment = document.createElement('link');
      styleElementForEnrichment.rel = 'stylesheet';
      styleElementForEnrichment.type = 'text/css';
      styleElementForEnrichment.href = linkForStyleSheetForEnrichment;
      styleElementForEnrichment.id = 'enrichment_style_id';
      document.head.appendChild(styleElementForEnrichment);
    }
  } else {
    if (styleElementForEnrichment) {
      styleElementForEnrichment.remove();
    }
  }
}



/**
 * Update the URL without refresh the page.
 *
 * @param {string} newUrl - The new URL.
 */
function updateUrl(newUrl) {
  history.pushState({}, document.title, newUrl);
}


/**
 * Refresh element with the DocumentFragment.
 *
 * @param {string} elementQuerySelector - The query selector for the element.
 * @param {Document} newHTMLContent - The parsed response fragment.
 * @param {boolean} optional - Whether a sidebar block may appear or disappear.
 */
function refreshElementWithDocumentFragment(elementQuerySelector, newHTMLContent, optional = false) {
  const newElement = newHTMLContent.querySelector(elementQuerySelector);
  const elementToRefresh = document.querySelector(elementQuerySelector);
  if (optional && !newElement) {
    elementToRefresh?.remove();
  } else if (optional && !elementToRefresh) {
    document.getElementById('collapseAside').appendChild(newElement.cloneNode(true));
  } else if (newElement && elementToRefresh) {
    elementToRefresh.innerHTML = newElement.innerHTML;
  }
}


/**
 * Scroll to the selected video.
 */
function scrollToSelectedVideo() {
  const scrollContainer = document.querySelector('.scroll-container');
  const selectedVideo = document.querySelector('.selected');
  if (selectedVideo && scrollContainer) {
    const containerRect = scrollContainer.getBoundingClientRect();
    const selectedRect = selectedVideo.getBoundingClientRect();
    const offsetTop = selectedRect.top - containerRect.top;
    scrollContainer.scrollTo({
      top: offsetTop,
      behavior: 'smooth'
    });
  }
}


/**
 * Get startCountDown() promise.
 * Used in video-script.html
 *
 * @returns The promise.
 */
function asyncStartCountDown() {
  return new Promise(function (resolve) {
    startCountdown(resolve);
  });
}


/**
 * Start the count down.
 *
 * @param {function} callback - The function called when the countdown finishes.
 * @param {number} remaining - The number of seconds left for this transition.
 */
function startCountdown(callback, remaining = playlistCount) {
  countdownElement = document.getElementById('pod-video-countdown');
  if (countdownElement) countdownElement.textContent = remaining;
  if (remaining > 1) {
    setTimeout(function () {
      startCountdown(callback, remaining - 1);
    }, 1000);
  } else if (typeof callback === 'function') {
    callback();
  }
}


if (typeof videos === "undefined") {
  var videos = document.querySelectorAll('.player-element');
} else {
  videos = document.querySelectorAll('.player-element');
}
videos.forEach(function (video) {
  new MutationObserver(scrollToSelectedVideo).observe(video, { attributes: true, attributeFilter: ['class'] });
});

document.addEventListener('DOMContentLoaded', function () {
  setTimeout(function () {
    scrollToSelectedVideo();
  }, 500);
});

var countdownElement = document.getElementById('pod-video-countdown');
