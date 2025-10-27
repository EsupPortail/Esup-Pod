/**
 * @file Esup-Pod script for instance of FilterManager in video dashboard.
 *
 * @since 4.1.0
 */


/**
 * @typedef {Object} FilterItem
 * @property {string} label - The display name shown in the UI
 * @property {string} value - The internal value used for filtering (e.g., slug)
 * Array of filter configurations to be used in FilterManager.
 * Each object defines how a specific filter behaves and how items are displayed and matched.
 * @type {Array<Object>}
 */
const filtersConfig = [
  {
    name: gettext("User"),
    param: "owner",
    searchCallback: getOwnersForVideosOnDashboard,
    itemLabel: user =>
      user.first_name && user.last_name
        ? `${user.first_name} ${user.last_name} (${user.username})`
        : user.username,
    itemKey: user => user.username,
  },
  {
    name: gettext("Type"),
    param: "type",
    searchCallback: (term) => fetchSingleFilter("type", term),
    itemLabel: type => type.label,
    itemKey: type => type.value,
  },
  {
    name: gettext("Discipline"),
    param: "discipline",
    searchCallback: (term) => fetchSingleFilter("discipline", term),
    itemLabel: discipline => discipline.label,
    itemKey: discipline => discipline.value,
  },
  {
    name: gettext("Tag"),
    param: "tag",
    searchCallback: (term) => fetchSingleFilter("tag", term),
    itemLabel: tag => tag.label,
    itemKey: tag => tag.value,
  },
  {
    name: gettext("Category"),
    param: "categories",
    searchCallback: (term) => fetchSingleFilter("categories", term),
    itemLabel: categories => categories.label,
    itemKey: categories => categories.value,
  }
];


/**
 * Retrieves the list of video owners based on a search term.
 * @async
 * @function
 * @param {string} searchTerm - The term used to search for owners.
 * @returns {Promise<Object[]>} - A promise that resolves to a list of matching users.
 */
async function getOwnersForVideosOnDashboard(searchTerm) {
  try {
    let data = new FormData();
    data.append("term", searchTerm);
    data.append("csrfmiddlewaretoken", Cookies.get("csrftoken"));
    const response = await fetch(DASHBOARD_OWNERS_URL, {
      method: "POST",
      body: data,
      headers: {
        Accept: "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
    });
    const users = await response.json();
    return users;
  } catch (error) {
    showalert(gettext("User not found"), "alert-danger");
  }
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
 * Retrieves a specific filter by its name.
 * @param {string} filterName
 * @returns {Promise<Object>}
 */
async function fetchSingleFilter(filterName, searchTerm = '') {
  let url = AVAILABLE_FILTER_URL.replace('FILTER_NAME_PLACEHOLDER', encodeURIComponent(filterName));
  if (searchTerm && searchTerm.trim() !== '') {
    url += url.includes('?') ? '&' : '?';
    url += `term=${encodeURIComponent(searchTerm.trim())}`;
  }

  const requestOptions = {
    method: "GET",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "Content-Type": "application/json"
    },
    credentials: "include" 
  };

  try {
    const response = await fetch(url, requestOptions);
    if (!response.ok) {
      throw new Error(`HTTP Error ${response.status}: ${response.statusText}`);
    }
    const data = await response.json();
    const key = filterName.toLowerCase(); 
    if (!data || typeof data !== 'object' || !Array.isArray(data[key])) {
      console.error("Malformed API response:", data);
      throw new Error(`Malformed API response: missing or invalid array for key '${key}'`);
    }
    // Map the received data to the { label, value } format expected by FilterManager
    return data[key].map(item => ({
      label: item.title || item.name || item.label || "unknown",
      value: item.id || item.slug || item.value || "unknown"
    }));

  } catch (error) {
    console.error(`Error fetching filter '${filterName}' with term '${searchTerm}' from ${url}:`, error);
    return [];
  }
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
