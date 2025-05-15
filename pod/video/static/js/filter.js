/**
 * @typedef {Object} FilterItem
 * @property {string} label - The display name shown in the UI
 * @property {string} value - The internal value used for filtering (e.g., slug)
 */

/** @type {FilterItem[]} */
let typeList = [];

/** @type {FilterItem[]} */
let disciplineList = [];

/** @type {FilterItem[]} */
let tagList = [];

/** @type {FilterItem[]} */
let categoryList = [];

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
    searchCallback: term => searchInList(typeList, term),
    itemLabel: type => type.label,
    itemKey: type => type.value,
  },
  {
    name: gettext("Discipline"),
    param: "discipline",
    searchCallback: term => searchInList(disciplineList, term),
    itemLabel: discipline => discipline.label,
    itemKey: discipline => discipline.value,
  },
  {
    name: gettext("Tag"),
    param: "tag",
    searchCallback: term => searchInList(tagList, term),
    itemLabel: tag => tag.label,
    itemKey: tag => tag.value,
  },
  {
    name: gettext("Catégorie"),
    param: "categories",
    searchCallback: term => searchInList(categoryList, term),
    itemLabel: category => category.label,
    itemKey: category => category.value,
  }
];

/**
 * Searches within a list of filter items by a search term, prioritizing matches first.
 *
 * @param {FilterItem[]} list - The list of filter items to search.
 * @param {string} searchTerm - The user-provided search input.
 * @returns {Promise<FilterItem[]>} A promise resolving to an ordered list of matched items.
 */
function searchInList(list, searchTerm) {
  return new Promise(resolve => {
    const normalizedTerm = searchTerm.trim().toLowerCase();
    if (!normalizedTerm) return resolve(list);

    const matching = [];
    const nonMatching = [];

    try {
      for (const item of list) {
        if (item.label.toLowerCase().includes(normalizedTerm)) {
          matching.push(item);
        } else {
          nonMatching.push(item);
        }
      }
    } catch (err) {
      console.error(`Error in filter.js (searchInList) while processing list: ${err.message || err}`);
    }

    resolve([...matching, ...nonMatching]);
  });
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
  try {
    const res = await fetch(urlAvailableFilters, {
      headers: { "X-Requested-With": "XMLHttpRequest" }
    });
    if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
    const data = await res.json();
    if (data.types) {
      typeList = data.types.map(type => ({
        label: gettext(type.title),
        value: type.slug
      }));
    }
    if (data.disciplines) {
      disciplineList = data.disciplines.map(discipline => ({
        label: gettext(discipline.title),
        value: discipline.slug
      }));
    }
    if (data.tags) {
      tagList = data.tags.map(tag => ({
        label: gettext(tag.name),
        value: tag.slug
      }));
    }
    if (data.category) {
      categoryList = Object.keys(data.category).map(slug => ({
        label: gettext(cleanLabel(slug)),
        value: slug
      }));
    }
  } catch (err) {
    console.error(`Error in filter.js (initFilters function) while fetching or processing data: ${err.message || err}\nStack trace: ${err.stack || 'No stack trace available'}`);
  }
}

/**
 * Detects a click event on the filters dropdown container.
 * When any filter dropdown inside is clicked, triggers the `initFilters` function.
 */
document.getElementById("filtersBox").addEventListener("click", initFilters);

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
