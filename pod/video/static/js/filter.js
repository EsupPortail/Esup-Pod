/**
 * @typedef {Object} FilterItem
 * @property {string} label - The display name shown in the UI
 * @property {string} value - The internal value used for filtering (e.g., slug)
 */

/**
 * Array of filter configurations to be used in FilterManager.
 * Each object defines how a specific filter behaves and how items are displayed and matched.
 * @type {Array<Object>}
 */
const filtersConfig = [
  {
    name: gettext("User"),
    param: "owner",
    searchCallback: getSearchListUsers,
    itemLabel: user =>
      user.first_name && user.last_name
        ? `${user.first_name} ${user.last_name} (${user.username})`
        : user.username,
    itemKey: user => user.username,
  },
  {
    name: gettext("Type"),
    param: "type",
    searchCallback: (term) => searchInList("type", term),
    itemLabel: type => type.label,
    itemKey: type => type.value,
  },
  {
    name: gettext("Discipline"),
    param: "discipline",
    searchCallback: (term) => searchInList("discipline", term),
    itemLabel: discipline => discipline.label,
    itemKey: discipline => discipline.value,
  },
  {
    name: gettext("Tag"),
    param: "tag",
    searchCallback: (term) => searchInList("tag", term),
    itemLabel: tag => tag.label,
    itemKey: tag => tag.value,
  },
  {
    name: gettext("Categories"),
    param: "categories",
    searchCallback: (term) => searchInList("categories", term),
    itemLabel: categories => categories.label,
    itemKey: categories => categories.value,
  }
];

/**
 * Searches within a list of filter items by a search term, prioritizing matches first.
 *
 * @param {FilterItem[]} list - The list of filter items to search.
 * @param {string} searchTerm - The user-provided search input.
 * @returns {Promise<FilterItem[]>} A promise resolving to an ordered list of matched items.
 */
async function searchInList(param, searchTerm) {
  let list;

  try {
    list = await fetchSingleFilter(param);
  } catch (err) {
    console.error(`Error in filter.js (searchInList) failed to fetch list: ${err.message || err}`);
    return [];
  }

  const normalizedTerm = searchTerm.trim().toLowerCase();
  if (!normalizedTerm) return list;

  const matching = [];
  const nonMatching = [];

  for (const item of list) {
    if (item.label.toLowerCase().includes(normalizedTerm)) {
      matching.push(item);
    } else {
      nonMatching.push(item);
    }
  }

  return [...matching, ...nonMatching];
}

// Initialize the filter manager
const filterManager = new FilterManager({
  filtersBoxId: 'filtersBox',
  activeFiltersId: 'selectedTags',
  resetFiltersId: 'filterTags'
});

// Inject filter configuration into the manager
filtersConfig.forEach(cfg => filterManager.addFilter(cfg));
filterManager.initializeFilters();

/**
 * Initializes filters by fetching data from the statistics API and preparing
 * the internal filter lists for types, disciplines, and tags.
 *
 * @async
 * @function
 * @returns {Promise<void>}
 */
async function initFilters() {
  const res = await fetch(AVAILABLE_FILTERS_URL, {
    method: "GET",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      'Content-Type': 'application/json'
    },
    credentials: "include"
  });
  if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
  return data = await res.json();
}

/**
 * Récupère un filtre spécifique par son nom.
 * @param {string} filterName
 * @returns {Promise<Object>}
 */
async function fetchSingleFilter(filterName) {
  const url = AVAILABLE_FILTER_URL.replace('FILTER_NAME_PLACEHOLDER', encodeURIComponent(filterName));
  const res = await fetch(url, { method: "GET", headers: { "X-Requested-With": "XMLHttpRequest", "Content-Type": "application/json" }, credentials: "include" });
  if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
  const data = await res.json();
  const key = filterName.toLowerCase();
  if (!data[key] || !Array.isArray(data[key])) {
    throw new Error(`Malformed API response: missing array for key '${key}'`);
  }

  // Remapper pour correspondre à { label, value }
  return data[key].map(item => ({
    label: item.title || item.name || item.label || "unknown",
    value: item.id || item.value || item.slug || item.value || "unknown"
  }));
}

/**
 * Cleans a slug by removing the prefix before the first hyphen
 * and capitalizing the first letter of the remaining string.
 * @param {string} slug
 * @returns {string}
 */
function cleanLabel(slug) {
  const partie = slug.split('-').slice(1).join('-');
  if (!partie) return '';
  return partie.charAt(0).toUpperCase() + partie.slice(1);
}
