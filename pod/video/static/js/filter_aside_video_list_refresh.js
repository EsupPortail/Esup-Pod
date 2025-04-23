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

  checkedInputs.forEach((input) => {
    urlParams.append(input.name, input.value);
  });

  urlParams.set("page", "");

  return `${baseUrl}?${urlParams.toString()}`;
}

//---------------------------------------------//
//------------------WORKING--------------------//
//---------------------------------------------//

let checkedUsernames = new Set();
let currentSearchResults = []; // tableau d’objets { username, first_name, last_name }

/**
 * Add change event listener on inputs (filters, sort column and sort direction) to refresh video list
 * @param el
 */
function setListenerChangeInputs(el) {
  el.addEventListener("change", (e) => {
    console.log("Changement détecté sur : ", e.target.value);
    checkedInputs = [];
    disabledInputs(true);
    document
      .querySelectorAll("input[type=checkbox]:checked[class=form-check-input]")
      .forEach((e) => {
        checkedInputs.push(e);
        console.log("Mis à jour de checkedInputs dans setListenerChangeInputs : ", e.value);
      });
    refreshActiveFiltersElement();
    refreshVideosSearch();
  });
}

function refreshActiveFiltersElement() {
  console.log("Entrée dans refreshActiveFiltersElement");
  const container = document.getElementById("activeFilters");
  container.innerHTML = ""; // On vide d'abord
  checkedInputs.forEach((input) => {
    console.log("refreshActiveFiltersElement input: ", input.value);
    const tag = document.createElement("div");
    tag.className = "badge bg-primary text-light me-2 mb-2 p-2";
    tag.innerText = input.value;

    // Optionnel : bouton pour retirer le filtre
    const closeBtn = document.createElement("button");
    closeBtn.className = "btn-close btn-close-white ms-2";
    closeBtn.style.fontSize = "0.6rem";
    closeBtn.onclick = () => {
      input.checked = false;
      input.dispatchEvent(new Event("change")); // Déclenche à nouveau le changement
      console.log("Je retire le filtre pour l'utilisateur : ", input.value);
    };

    tag.appendChild(closeBtn);
    container.appendChild(tag);
  });
}

if (ownerBox) {
  const userFilterDropdown = document.getElementById("user-filter-dropdown");

  // Au clic sur le menu déroulant, on affiche les utilisateurs sélectionnés
  userFilterDropdown.addEventListener("click", () => {
    console.log("Menu déroulant cliqué, affichage des utilisateurs sélectionnés");
    displayCheckedUsers();
  });

  // Au changement dans l'input de recherche
  ownerBox.addEventListener("input", () => {
    const searchTerm = ownerBox.value;
    console.log("Recherche en cours avec le terme : ", searchTerm);

    if (searchTerm && searchTerm.length > 2) {
      console.log("Termes de recherche trouvés, appel à getSearchListUsers()");
      // Si l'utilisateur tape quelque chose, on effectue une recherche
      getSearchListUsers(searchTerm).then((users) => {
        updateUserList(users);
      });
    } else {
      console.log("Recherche vide, affichage uniquement des utilisateurs sélectionnés");
      // Sinon, on affiche uniquement les utilisateurs sélectionnés
      displayCheckedUsers();
    }
  });
}

// Affiche uniquement les utilisateurs sélectionnés
function displayCheckedUsers() {
  console.log("Affichage des utilisateurs sélectionnés...");
  const selectedUsernames = new Set(checkedInputs.map(u => u.value));

  if (selectedUsernames.size === 0) {
    console.log("Aucun utilisateur sélectionné, vider le container");
    filterOwnerContainer.textContent = "";
    return;
  }

  console.log("Utilisateurs sélectionnés : ", Array.from(selectedUsernames));

  // On effectue une recherche vide (qui renvoie tous les utilisateurs)
  getSearchListUsers("").then((users) => {
    const selectedUsers = users.filter(user => selectedUsernames.has(user.username));
    updateUserList(selectedUsers);
  });
}

function updateUserList(users) {
  console.log("Mise à jour de la liste des utilisateurs...");
  filterOwnerContainer.textContent = ""; // Vider l'affichage précédent

  // Récupérer les utilisateurs sélectionnés
  const selectedUsernames = new Set(checkedInputs.map(u => u.value));

  // Filtrer les utilisateurs pour ceux qui correspondent à la recherche
  const filteredUsers = users.filter(user => !selectedUsernames.has(user.username));

  console.log("Utilisateurs filtrés : ", filteredUsers);

  // Fusionner les utilisateurs sélectionnés et filtrés (les sélectionnés viennent en premier)
  const finalUserList = [
    ...checkedInputs.map(input => ({
      username: input.value,
      first_name: "", // Remplir si nécessaire
      last_name: "",  // Remplir si nécessaire
    })),
    ...filteredUsers
  ];

  const fragment = document.createDocumentFragment();

  // Ajouter chaque utilisateur dans le DOM
  finalUserList.forEach((user) => {
    const checkboxId = "id" + user.username;
    if (!document.getElementById(checkboxId)) {
      console.log("Ajout de l'utilisateur au DOM : ", user.username);
      const checkbox = createUserCheckBox(user, selectedUsernames);
      fragment.appendChild(checkbox);
      setListenerChangeInputs(checkbox.querySelector("input"));
    }
  });

  filterOwnerContainer.appendChild(fragment);
}


/**
 * Create checkbox for user search
 * @param user
 * @returns {HTMLDivElement}
 */
function createUserCheckBox(user, selectedUsernames) {
  console.log("Création de la checkbox pour l'utilisateur : ", user.username);
  let div = document.createElement("div");
  div.classList.add("form-check");

  let checkbox = document.createElement("input");
  checkbox.classList.add("form-check-input");
  checkbox.type = "checkbox";
  checkbox.name = "owner";
  checkbox.value = user.username;
  checkbox.id = "id" + user.username;

  // Coche si utilisateur déjà sélectionné
  if (selectedUsernames.has(user.username)) {
    checkbox.checked = true;
    console.log("Utilisateur sélectionné : ", user.username);
  }

  let label = document.createElement("label");
  label.classList.add("form-check-label");
  label.setAttribute("for", checkbox.id);

  const fullName = `${user.first_name} ${user.last_name}`.trim();
  label.innerHTML = (fullName !== "" ? fullName + " " : "") + `(${user.username})`;

  div.appendChild(checkbox);
  div.appendChild(label);

  console.log("Checkbox créée pour : ", user.username);

  return div;
}



/**
 * Add click event listener to manage reset of filters
 */
document.getElementById("resetFilters").addEventListener("click", function () {
  checkedInputs = [];
  document
    .querySelectorAll("#filters input[type=checkbox]:checked[class=form-check-input]")
    .forEach((checkBox) => {
      checkBox.checked = false;
    });

  document.querySelectorAll("#filters .categories-list-item").forEach((c_p) => {
    c_p.classList.remove("active");
  });

  document.getElementById("titlebox").value = "";
  if (filterOwnerContainer && ownerBox) {
    filterOwnerContainer.textContent = "";
    ownerBox.value = "";
  }

  window.history.pushState("", "", window.location.pathname);
  refreshVideosSearch();
});

let teststst = document.querySelectorAll("input[type=checkbox]:checked[class=form-check-input]");
console.log("Resutat querySelectorAll l370 : " + teststst.entries());
checkedInputs = [];
teststst.forEach((e) => {
    checkedInputs.push(e);
    console.log("Mis a jours de checkedInputs l370 : "+e.value);
  });
refreshActiveFiltersElement();

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
