/**
 * @file Esup-Pod functions for videos list refresh and aside manage.
 * @since 3.4.1
 */

// Read-only globals defined in filter-aside-element-list-refresh.js
/* global toggleSortDirection */

// Read-only globals defined ever in playlist.html, dashboard.html or videos.html
/* global urlVideos */

// Read-only globals defined ever in infinite.js
/* global InfiniteLoader */

// Read-only globals defined in video_select.js
/* global setSelectedVideos */


var infinite;

let infiniteLoading = document.querySelector(".infinite-loading");

function onBeforePageLoad() {
  infiniteLoading.style.display = "block";
}
function onAfterPageLoad() {
  if (
    urlVideos === "/video/dashboard/" &&
    selectedVideos[videosListContainerId] &&
    selectedVideos[videosListContainerId].length !== 0
  ) {
    setSelectedVideos(videosListContainerId);
  }
  infiniteLoading.style.display = "none";
  let footer = document.querySelector("footer.static-pod");
  if (!footer) return;
  footer.classList.add("small");
  footer.classList.add("fixed-bottom");
  footer.setAttribute("style", "height:80px; overflow-y:auto");
  var docHeight = Math.max(
    document.body.scrollHeight,
    document.body.offsetHeight,
    document.clientHeight,
    document.scrollHeight,
    document.offsetHeight,
  );
  document.querySelector("footer.static-pod .hidden-pod").style.display =
    "none";
  window.addEventListener("scroll", function () {
    if (window.innerHeight + window.scrollTop() === docHeight) {
      document.querySelector("footer.static-pod .hidden-pod").style.display =
        "block";
      footer.setAttribute("style", "height:auto;");
      footer.classList.remove("fixed-bottom");
    }
  });
}

/**
 * Refresh Infinite Loader (Waypoint Infinite's)
 * @param url
 * @param nextPage
 */
function refreshInfiniteLoader(url, nextPage) {
  if (infinite !== undefined) {
    infinite.removeLoader();
  }
  infinite = null;
  infinite = new InfiniteLoader(
    url,
    onBeforePageLoad,
    onAfterPageLoad,
    (page = nextPage),
  );
}

/**
 * Replace count videos label (h1) with translation and plural
 * @param newCount
 */
function replaceCountVideos(newCount) {
  let videoFoundStr = ngettext(
    "%(count)s video found",
    "%(count)s videos found",
    newCount,
  );
  videoFoundStr = interpolate(videoFoundStr, { count: newCount }, true);
  document.getElementById("video_count").textContent = videoFoundStr;
}

/**
 * Add click event listener to manage sort direction
 */
const sortDirectionLabel = document.getElementById("sort_direction_label");

if (sortDirectionLabel) {
  sortDirectionLabel.addEventListener("click", function (e) {
    e.preventDefault();
    toggleSortDirection();
    refreshVideosSearch();
  });
}

/**
 * Handles the search form submission.
 * Prevents default behavior, gets the title input,
 */
document.getElementById("searchForm").addEventListener("submit", function (e) {
  e.preventDefault();
  refreshVideosSearch();
});

/**
 * Retrieves the current value entered in the video title search input field.
 *
 * @returns {string} The current value of the search input with ID "titlebox".
 */
function getSearchValue() {
  return document.getElementById("titlebox").value;
}
/*
 * Async request to refresh view with filtered and sorted video list
 */
function refreshVideosSearch() {
  // Erase videos list and show loader
  document.getElementById("videos_list").textContent = "";
  showLoader(videosListLoader, true);
  let url = getUrlForRefresh();
  // Async GET request wth parameters by fetch method
  fetch(url, {
    method: "GET",
    headers: {
      "X-CSRFToken": "{{ csrf_token }}",
      "X-Requested-With": "XMLHttpRequest",
    },
    dataType: "html",
    cache: "no-store",
  })
    .then((response) => response.text())
    .then((data) => {
      // parse data into html and replace videos list
      let parser = new DOMParser();
      let html = parser.parseFromString(data, "text/html").body;
      document.getElementById("videos_list").outerHTML = html.innerHTML;
      replaceCountVideos(
        document.getElementById("videos_list").dataset.countvideos,
      );
      nextPage =
        document.getElementById("videos_list").dataset.nextpage === "true";
      window.history.pushState({}, "", url);
      if (nextPage) {
        pageNext = document.querySelector("a.infinite-more-link").dataset
          .nextpagenumber;
        refreshInfiniteLoader(url, pageNext);
      }
      if (
        urlVideos === "/video/dashboard/" &&
        selectedVideos[videosListContainerId] &&
        selectedVideos[videosListContainerId].length !== 0
      ) {
        setSelectedVideos(videosListContainerId);
      }
    })
    .catch(() => {
      document.getElementById("videos_list").textContent = gettext(
        "An Error occurred while processing.",
      );
    })
    .finally(() => {
      // Finally re-enable inputs and dismiss loader
      disabledInputs(false);
      showLoader(videosListLoader, false);
    });
}

// Fonction pour récupérer l'URL pour rafraîchir la page avec les filtres appliqués
function getUrlForRefresh() {
  const baseUrl = window.location.pathname;
  const urlParams = new URLSearchParams(window.location.search);

  const sort = document.getElementById("sort")?.value;
  if (sort) {
    urlParams.set("sort", sort);
  } else {
    urlParams.delete("sort");
  }

  const sortDirectionEl = document.getElementById("sort_direction");
  if (sortDirectionEl?.checked) {
    urlParams.set("sort_direction", sortDirectionEl.value);
  } else {
    urlParams.delete("sort_direction");
  }

  const newTitle = getSearchValue();
  if (newTitle) {
    urlParams.set("title", newTitle);
  } else {
    urlParams.delete("title");
  }

  if (typeof displayMode !== "undefined") {
    urlParams.set("display_mode", displayMode);
  }

  urlParams.delete("categories");
  document.querySelectorAll(".categories-list-item.active").forEach((cat) => {
    const slug = cat.firstElementChild?.dataset.slug;
    if (slug) {
      urlParams.append("categories", slug);
    }
  });

  urlParams.delete("page");
  return `${baseUrl}?${urlParams.toString()}`;
}

// Fonction pour activer ou désactiver les cases à cocher pendant le chargement
function disabledInputs(value) {
  document.querySelectorAll("input.form-check-input").forEach(cb => cb.disabled = value);
}

// First launch of the infinite scroll
infinite = new InfiniteLoader(
  getUrlForRefresh(),
  onBeforePageLoad,
  onAfterPageLoad,
  nextPage,
  (page = 2),
);

// Check and clean url to avoid owner parameter if not authorized
var urlParams = new URLSearchParams(window.location.search);
if (urlParams.has("owner") && !ownerFilter) {
  urlParams.delete("owner");
  window.history.pushState(
    null,
    "",
    location.protocol +
      "//" +
      location.host +
      location.pathname +
      urlParams.toString(),
  );
}

