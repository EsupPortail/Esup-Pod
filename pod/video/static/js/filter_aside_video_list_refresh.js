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
var checkedInputs = [];

let infiniteLoading = document.querySelector(".infinite-loading");
let ownerBox = document.getElementById("ownerbox");
let filterOwnerContainer = document.getElementById("collapseFilterOwner");

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

/**
 * Add click event listener to manage sort direction
 */
document
  .getElementById("sort_direction_label")
  .addEventListener("click", function (e) {
    e.preventDefault();
    toggleSortDirection();
    refreshVideosSearch();
  });

/**
 * Get built url with filter and sort and page parameters
 * @returns {string}
 */
function getUrlForRefresh() {
  let newUrl = window.location.pathname;
  // Add sort-related parameters
  newUrl += "?sort=" + document.getElementById("sort").value + "&";
  var sortDirectionAsc = document.getElementById("sort_direction").checked;

  if (sortDirectionAsc) {
    newUrl +=
      "sort_direction=" + document.getElementById("sort_direction").value + "&";
  }
  // Add dashboard display mode param
  if (urlVideos === "/video/dashboard/" && displayMode !== undefined) {
    newUrl += "display_mode=" + displayMode + "&";
  }
  // Add categories checked if exists
  if (document.querySelectorAll(".categories-list-item.active").length !== 0) {
    Array.from(
      document.querySelectorAll(".categories-list-item.active"),
    ).forEach((cat) => {
      newUrl += "categories=" + cat.firstElementChild["dataset"]["slug"] + "&";
    });
  }
  // Add all other parameters (filters)
  checkedInputs.forEach((input) => {
    newUrl += input.name + "=" + input.value + "&";
  });
  // Add page parameter
  newUrl += "page=";
  return newUrl;
}

/**
 * Add change event listener on inputs (filters, sort column and sort direction) to refresh video list
 * @param el
 */
function setListenerChangeInputs(el) {
  el.addEventListener("change", (e) => {
    checkedInputs = [];
    disabledInputs(true);
    document
      .querySelectorAll("input[type=checkbox]:checked[class=form-check-input]")
      .forEach((e) => {
        checkedInputs.push(e);
      });
    refreshVideosSearch();
  });
}

/**
 * Add event listener to search user input to create checkboxes
 */
if (ownerBox) {
  ownerBox.addEventListener("input", () => {
    if (ownerBox.value && ownerBox.value.length > 2) {
      var searchTerm = ownerBox.value;
      getSearchListUsers(searchTerm).then((users) => {
        filterOwnerContainer.textContent = "";
        users.forEach((user) => {
          filterOwnerContainer.appendChild(createUserCheckBox(user));
          setListenerChangeInputs(
            document.getElementById("id" + user.username),
          );
        });
      });
    } else {
      filterOwnerContainer.textContent = "";
    }
  });
}

/**
 * Create checkbox for user search
 * @param user
 * @returns {HTMLDivElement}
 */
function createUserCheckBox(user) {
  let div = document.createElement("div");
  div.classList.add("form-check");
  let checkbox = document.createElement("input");
  checkbox.classList.add("form-check-input");
  checkbox.type = "checkbox";
  checkbox.name = "owner";
  checkbox.value = user.username;
  checkbox.id = "id" + user.username;
  let label = document.createElement("label");
  label.classList.add("form-check-label");
  label.setAttribute("for", "id" + user.username);
  if (user.first_name !== "" && user.last_name !== "") {
    label.innerHTML = user.first_name + " " + user.last_name + " ";
  }
  label.innerHTML += "(" + user.username + ")";
  div.appendChild(checkbox);
  div.appendChild(label);
  return div;
}

/**
 * Add click event listener to manage reset of filters
 */
document.getElementById("resetFilters").addEventListener("click", function () {
  checkedInputs = [];
  document
    .querySelectorAll(
      "#filters input[type=checkbox]:checked[class=form-check-input]",
    )
    .forEach((checkBox) => {
      checkBox.checked = false;
    });
  document.querySelectorAll("#filters .categories-list-item").forEach((c_p) => {
    c_p.classList.remove("active");
  });
  if (filterOwnerContainer && ownerBox) {
    filterOwnerContainer.textContent = "";
    ownerBox.value = "";
  }
  window.history.pushState("", "", window.location.pathname);
  refreshVideosSearch();
});

/**
 * Toggle (enable/disable) inputs to prevent user actions during loading
 * @param value
 */
function disabledInputs(value) {
  document
    .querySelectorAll("input[type=checkbox][class=form-check-input]")
    .forEach((checkbox) => {
      checkbox.disabled = value;
    });
}

document
  .querySelectorAll("#filters .form-check-input,#sort,#sort_direction")
  .forEach((el) => {
    setListenerChangeInputs(el);
  });

document
  .querySelectorAll("input[type=checkbox]:checked[class=form-check-input]")
  .forEach((e) => {
    checkedInputs.push(e);
  });

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
