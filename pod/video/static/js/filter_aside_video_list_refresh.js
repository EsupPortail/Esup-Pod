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
let filtersState = {};

const categorySet = new Set([
  "Mathématiques",
  "Biologie",
  "Physique",
  "Histoire",
  "Informatique",
  "Mathématiques2",
  "Biologie2",
  "Physique2",
  "Histoire2",
  "Informatique2",
]);

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

  Object.keys(filtersState).forEach(param => {
    urlParams.delete(param);

    const filter = filtersState[param];
    filter.selectedItems.forEach((value, key) => {
      urlParams.append(param, key);
    });
  });

  urlParams.delete("page");
  return `${baseUrl}?${urlParams.toString()}`;
}


function saveFiltersToSession() {
  Object.entries(filtersState).forEach(([param, filter]) => {
    const itemsArray = Array.from(filter.selectedItems.values());
    sessionStorage.setItem(param, JSON.stringify(itemsArray));
  });
}

function initializeFiltersFromSession() {
  Object.entries(filtersState).forEach(([param, filter]) => {
    const raw = sessionStorage.getItem(param);
    if (raw) {
      const items = JSON.parse(raw);
      items.forEach(item => {
        const key = filter.itemKey(item);
        filter.selectedItems.set(key, item);
      });
    }
    renderFilter(param);
  });
}

function setListenerChangeInputs(inputEl, param, item) {
  const state = filtersState[param];
  const key = state.itemKey(item);
  inputEl.addEventListener("change", () => {
    if (inputEl.checked) {
      state.selectedItems.set(key, item);
    } else {
      state.selectedItems.delete(key);
    }

    renderFilter(param);
    updateSelectedTags();
    refreshVideosSearch();
    saveFiltersToSession();
  });
}

// Fonction d'initialisation des filtres à partir de l'URL ou de la session
document.addEventListener("DOMContentLoaded", () => {
  // Initialiser les filtres à partir de la session
  initializeFiltersFromSession();

  // Mettre à jour les tags sélectionnés après l'initialisation des filtres
  updateSelectedTags();
});

document.getElementById("filterTags").addEventListener("click", (e) => {
  e.preventDefault();
  clearAllFilters();
});

function clearAllFilters() {
  Object.values(filtersState).forEach(filter => filter.selectedItems.clear());
  document.querySelectorAll(".categories-list-item.active").forEach(item => {
    item.classList.remove("active");
  });
  Object.keys(filtersState).forEach(param => {
    sessionStorage.removeItem(param);
  });
  var input = document.getElementById("search_input");
  if (input) input.value = "";
  updateSelectedTags();
  Object.keys(filtersState).forEach(renderFilter);
  const baseUrl = window.location.pathname;
  window.history.replaceState(null, "", baseUrl);
  refreshVideosSearch();
}


// Rendre les éléments de filtre à partir des données et de l'état
function renderFilter(param) {
  const state = filtersState[param];
  const listContainer = document.getElementById(`collapseFilter${capitalize(param)}`);
  listContainer.innerHTML = "";

  const orderedItems = [
    ...state.selectedItems.values(),
    ...state.searchResults.filter(item => !state.selectedItems.has(state.itemKey(item)))
  ];

  const frag = document.createDocumentFragment();
  orderedItems.forEach(item => {
    const checkboxDiv = renderItem(item, state.selectedItems, state.itemLabel, param);
    frag.appendChild(checkboxDiv);
  });
  listContainer.appendChild(frag);
}

// Rendre chaque élément de filtre (checkbox + label)
function renderItem(item, selectedSet, itemLabel, param) {
  const div = document.createElement("div");
  div.classList.add("form-check");

  const key = filtersState[param].itemKey(item);

  const checkbox = document.createElement("input");
  checkbox.classList.add("form-check-input");
  checkbox.type = "checkbox";
  checkbox.name = key;
  checkbox.value = key;
  checkbox.id = `id-${param}-${key}`;
  checkbox.checked = selectedSet.has(key);

  setListenerChangeInputs(checkbox, param, item);

  const label = document.createElement("label");
  label.classList.add("form-check-label");
  label.setAttribute("for", checkbox.id);
  label.textContent = itemLabel(item);

  div.appendChild(checkbox);
  div.appendChild(label);
  return div;
}

/**
 * Ajoute un filtre dynamique à l'interface.
 * @param {Object} filterInfo Infos sur le filtre à ajouter
 */
function addFilter({ name, param, searchCallback, itemLabel, itemKey }) {
  const slug = slugify(name);  // Créer un identifiant "propre" pour chaque filtre
  const filterId = `${slug}-filter-dropdown`;

  // Créer et ajouter le bloc de filtre dans le DOM
  const filterEl = createFilter(name, param, slug, filterId);
  console.log(filterEl.innerHTML);
  const filtersBoxEl = document.getElementById("filtersBox");
  console.log(filtersBoxEl.innerHTML);
  filtersBoxEl.appendChild(filterEl);
  console.log(filtersBoxEl.innerHTML);

  filtersState[param] = {
    selectedItems: new Map(),
    searchResults: [],
    getSearch: searchCallback,
    itemLabel,
    itemKey
  };

  const inputBox = document.getElementById(`${slug}box`);
  const dropdownBtn = document.getElementById(filterId);

  // Affiche tous les résultats lors du clic sur le bouton du dropdown
  dropdownBtn.addEventListener("click", () => {
    // Si tu veux afficher tous les éléments, utilise getSearch pour obtenir tous les éléments
    filtersState[param].getSearch('')
      .then(results => {
        // Assigner tous les résultats à searchResults
        filtersState[param].searchResults = results;
        renderFilter(param);
      });
  });

  // Recherche dynamique via le champ de recherche
  inputBox.addEventListener("input", () => {
    const term = inputBox.value.trim();
    disabledInputs(true);  // Désactive les entrées pendant la recherche
    filtersState[param].getSearch(term)
      .then(results => {
        filtersState[param].searchResults = results;
        renderFilter(param);
      })
      .finally(() => disabledInputs(false));

    filtersState[param].searchResults = [];
    renderFilter(param);
  });
}


this.addFilter({
  name: "Utilisateur",
  param: "owner",
  searchCallback: getSearchListUsers,
  itemLabel: (u) => {
    const hasFullName = u.first_name && u.last_name;
    return hasFullName
      ? `${u.first_name} ${u.last_name} (${u.username})`
      : u.username;
  },
  itemKey: (u) => u.username
});

this.addFilter({
  name: "Disciplines",
  param: "disciplines",
  searchCallback: (searchTerm) => searchInSet(categorySet, searchTerm),
  itemLabel: (category) => category,
  itemKey: (category) => category
});

console.log(filtersState);

function updateSelectedTags() {
  const selectedTagsContainer = document.getElementById("selectedTags");

  // Effacer les tags existants
  selectedTagsContainer.innerHTML = "";

  // Ajouter de nouveaux tags
  Object.entries(filtersState).forEach(([param, filter]) => {
    filter.selectedItems.forEach(item => {
      const label = filter.itemLabel(item);
      const key = filter.itemKey(item);

      const tag = document.createElement("div");
      tag.className = "badge bg-primary text-white d-inline-flex align-items-center me-2 mb-2 p-2";

      const text = document.createElement("span");
      text.textContent = label;
      tag.appendChild(text);

      const closeBtn = document.createElement("button");
      closeBtn.type = "button";
      closeBtn.className = "btn-close btn-close-white btn-sm ms-2";
      closeBtn.setAttribute("aria-label", "Remove filter");
      closeBtn.onclick = () => {
        filter.selectedItems.delete(key);
        renderFilter(param);
        updateSelectedTags();
        refreshVideosSearch();
        saveFiltersToSession(); // Sauvegarder l'état après modification
      };
      tag.appendChild(closeBtn);

      selectedTagsContainer.appendChild(tag);
    });
  });
  console.log(filtersState);
}


/**
 * Crée un composant de filtre avec recherche et liste déroulante.
 * @param {string} name Le nom du filtre
 * @param {string} param Le paramètre du filtre
 * @param {string} slug L'identifiant unique du filtre
 * @param {string} filterId L'ID du filtre
 * @returns {HTMLDivElement} Le composant du filtre
 */
function createFilter(name, param, slug, filterId) {
  const dropdown = document.createElement('div');
  dropdown.className = 'dropdown';

  // Bouton du menu déroulant
  const button = document.createElement('button');
  button.id = filterId;
  button.className = 'btn btn-outline-primary dropdown-toggle';
  button.type = 'button';
  button.setAttribute('data-bs-toggle', 'dropdown');
  button.setAttribute('aria-expanded', 'false');
  button.innerText = name;

  // Menu déroulant
  const menu = document.createElement('div');
  menu.className = 'dropdown-menu p-2';
  menu.style.minWidth = '100px';

  // Groupe de recherche (input)
  const inputGroup = document.createElement('div');
  inputGroup.className = 'input-group mb-3';

  const input = document.createElement('input');
  input.placeholder = `Recherche par ${slug}`;
  input.id = `${slug}box`;
  input.type = 'text';
  input.className = 'form-control';
  inputGroup.appendChild(input);

  // Liste des éléments avec barre de défilement
  const listContainer = document.createElement('div');
  listContainer.className = `form-group navList ${slug}s`;
  listContainer.id = `collapseFilter${capitalize(param)}`;

  // Utilisation des classes Bootstrap pour gérer le défilement
  listContainer.classList.add('overflow-auto'); // Ajoute la classe Bootstrap pour scroll
  listContainer.style.maxHeight = '200px'; // Limite la hauteur du conteneur

  menu.appendChild(inputGroup);
  menu.appendChild(listContainer);
  dropdown.appendChild(button);
  dropdown.appendChild(menu);

  return dropdown;
}


/**
 * Active ou désactive toutes les cases à cocher pendant le chargement.
 * @param {boolean} value La valeur pour activer/désactiver les cases
 */
function disabledInputs(value) {
  document.querySelectorAll("input.form-check-input").forEach(cb => cb.disabled = value);
}

function searchInSet(originalSet, searchTerm) {
  return new Promise((resolve) => {
    const items = Array.from(originalSet);
    const normalizedTerm = searchTerm.trim().toLowerCase();

    if (!normalizedTerm) {
      return resolve(items);  // Retourne tout si la recherche est vide
    }

    const matching = [];
    const nonMatching = [];

    // Simule un délai (par exemple un appel API) avec setTimeout
    setTimeout(() => {
      for (const item of items) {
        if (item.toLowerCase().includes(normalizedTerm)) {
          matching.push(item);
        } else {
          nonMatching.push(item);
        }
      }
      // Retourne les éléments triés
      resolve([...matching, ...nonMatching]);
    }, 300);  // Délai simulé de 300ms
  });
}




//---------------------------------------------//
//----------------END-WORKING------------------//
//---------------------------------------------//




// document
//   .querySelectorAll("#filters .form-check-input,#sort,#sort_direction")
//   .forEach((el) => {
//     setListenerChangeInputs(el);
//   });

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

function slugify(nom) {
  return nom
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/\s+/g, '')
    .replace(/[^a-z0-9]/g, '');
}

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}