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

//---------------------------------------------//
//------------------WORKING--------------------//
//---------------------------------------------//

// État global
let checkedUsernames = new Set();
let currentSearchResults = []; // [{ username, first_name, last_name }]

/**
 * Get built url with filter and sort and page parameters
 * @returns {string}
 */
function getUrlForRefresh() {
  let baseUrl = window.location.pathname;
  let urlParams = new URLSearchParams(window.location.search);

  urlParams.set("sort", document.getElementById("sort").value);
  let sortDirectionAsc = document.getElementById("sort_direction").checked;
  if (sortDirectionAsc) {
    urlParams.set("sort_direction", document.getElementById("sort_direction").value);
  } else {
    urlParams.delete("sort_direction");
  }

  let newTitle = getSearchValue();
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
    urlParams.append("categories", cat.firstElementChild.dataset.slug);
  });

  urlParams.delete("owner");

  checkedUsernames.forEach(username => {
    urlParams.append("owner", username);
  });

  urlParams.set("page", "");

  return `${baseUrl}?${urlParams.toString()}`;
}

/**
 * Ajoute un listener change sur une checkbox et met à jour l'état + UI + vidéos
 * @param {HTMLInputElement} inputEl
 */
function setListenerChangeInputs(inputEl) {
  inputEl.addEventListener("change", () => {
    const username = inputEl.value;
    if (inputEl.checked) {
      checkedUsernames.add(username);
    } else {
      checkedUsernames.delete(username);
    }
    console.log(`Checkbox ${inputEl.checked ? 'cochée' : 'décochée'} pour : ${username}`);
    render();
    refreshVideosSearch();
  });
}

/**
 * Rendu unique : badges et liste de checkboxes
 */
function render() {
  // 1) Badges
  const badgeContainer = document.getElementById("activeFilters");
  badgeContainer.innerHTML = "";
  checkedUsernames.forEach(username => {
    const tag = document.createElement("div");
    tag.className = "badge bg-primary text-light me-2 mb-2 p-2";
    tag.innerText = username;

    const closeBtn = document.createElement("button");
    closeBtn.className = "btn-close btn-close-white ms-2";
    closeBtn.style.fontSize = "0.6rem";
    closeBtn.onclick = () => {
      checkedUsernames.delete(username);
      console.log(`Filtre retiré : ${username}`);
      render();
      refreshVideosSearch();
    };

    tag.appendChild(closeBtn);
    badgeContainer.appendChild(tag);
  });

  // 2) Checkboxes
  const listContainer = filterOwnerContainer;
  listContainer.innerHTML = "";

  // Construction de la liste : cochés d'abord, puis résultats
  const orderedUsers = [
    ...[...checkedUsernames].map(u => ({ username: u, first_name: "", last_name: "" })),
    ...currentSearchResults.filter(u => !checkedUsernames.has(u.username))
  ];

  const fragment = document.createDocumentFragment();
  orderedUsers.forEach(user => {
    const checkboxDiv = createUserCheckBox(user, checkedUsernames);
    fragment.appendChild(checkboxDiv);
    setListenerChangeInputs(checkboxDiv.querySelector("input.form-check-input"));
  });
  listContainer.appendChild(fragment);

  // Réactiver inputs
  disabledInputs(false);
}

// Initialisation des événements
if (ownerBox) {
  const userFilterDropdown = document.getElementById("user-filter-dropdown");

  // Affiche les cochés au clic sans vider
  userFilterDropdown.addEventListener("click", () => {
    currentSearchResults = [];
    console.log("Dropdown cliqué : affichage des cochés");
    render();
  });

  // Recherche live
  ownerBox.addEventListener("input", () => {
    const term = ownerBox.value.trim();
    if (term.length > 2) {
      console.log(`Recherche : ${term}`);
      disabledInputs(true);
      getSearchListUsers(term)
        .then(users => {
          currentSearchResults = users;
          render();
        })
        .catch(err => {
          console.error(err);
          disabledInputs(false);
        });
    } else {
      currentSearchResults = [];
      console.log("Recherche courte ou vide : reset des résultats");
      render();
    }
  });

  document.getElementById("filterTags").addEventListener("click", () => {
    checkedUsernames.clear();
    currentSearchResults = [];
    ownerBox.value = "";
    console.log("Reset de tous les filtres");
    render();
    refreshVideosSearch();
    window.history.pushState("", "", window.location.pathname);
  });
}

/**
 * Création d'un div.form-check avec input checkbox et label,
 * basé sur l'état sélectionné.
 * @param {{username:string, first_name:string, last_name:string}} user
 * @param {Set<string>} selectedSet
 */
function createUserCheckBox(user, selectedSet) {
  const div = document.createElement("div");
  div.classList.add("form-check");

  const checkbox = document.createElement("input");
  checkbox.classList.add("form-check-input");
  checkbox.type = "checkbox";
  checkbox.name = "owner";
  checkbox.value = user.username;
  checkbox.id = "id" + user.username;
  checkbox.checked = selectedSet.has(user.username);

  const label = document.createElement("label");
  label.classList.add("form-check-label");
  label.setAttribute("for", checkbox.id);
  const fullName = `${user.first_name} ${user.last_name}`.trim();
  label.textContent = fullName ? `${fullName} (${user.username})` : `(${user.username})`;

  div.appendChild(checkbox);
  div.appendChild(label);
  return div;
}

/**
 * Active ou désactive toutes les checkboxes pendant le chargement
 * @param {boolean} value
 */
function disabledInputs(value) {
  document.querySelectorAll("input.form-check-input").forEach(cb => cb.disabled = value);
}

//---------------------------------------------//
//----------------END-WORKING------------------//
//---------------------------------------------//


document
  .querySelectorAll("#filters .form-check-input,#sort,#sort_direction")
  .forEach((el) => {
    setListenerChangeInputs(el);
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
