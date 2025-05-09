let typeSet = new Set();
let disciplineSet = new Set();
let tagSet = new Set();

const filtersConfig = [
  {
    name: gettext("User"),
    param: "owner",
    searchCallback: getSearchListUsers,
    itemLabel: u =>
      u.first_name && u.last_name
        ? `${u.first_name} ${u.last_name} (${u.username})`
        : u.username,
    itemKey: u => u.username,
  },
  {
    name: "Types",
    param: "type",
    searchCallback: term => searchInSet(typeSet, term),
    itemLabel: type => type,
    itemKey: type => type,
  },
  {
    name: "Disciplines",
    param: "dicipline",
    searchCallback: term => searchInSet(disciplineSet, term),
    itemLabel: dicipline => dicipline,
    itemKey: dicipline => dicipline,
  },
  {
    name: "Tags",
    param: "tag",
    searchCallback: term => searchInSet(tagSet, term),
    itemLabel: tag => tag,
    itemKey: tag => tag,
  }
];

const filterManager = new FilterManager({
  filtersBoxId: 'filtersBox',
  activeFiltersId: 'selectedTags',
  resetFiltersId: 'filterTags'
});

filtersConfig.forEach(cfg => filterManager.addFilter(cfg));
filterManager.initializeFilters();


/**
 * Simulates a fetch operation by searching within a Set.
 * Returns a Promise that resolves with the items sorted by match relevance.
 *
 * @param {Set<string>} originalSet - The set of strings to search in.
 * @param {string} searchTerm - The term to search for.
 * @returns {Promise<string[]>} A Promise resolving to an array of strings sorted by relevance.
 */
function searchInSet(originalSet, searchTerm) {
  return new Promise((resolve) => {
    const items = Array.from(originalSet);
    const normalizedTerm = searchTerm.trim().toLowerCase();

    if (!normalizedTerm) {
      return resolve(items);
    }

    const matching = [];
    const nonMatching = [];

    setTimeout(() => {
      for (const item of items) {
        if (item.toLowerCase().includes(normalizedTerm)) {
          matching.push(item);
        } else {
          nonMatching.push(item);
        }
      }
      resolve([...matching, ...nonMatching]);
    }, 100);
  });
}

async function initFilters() {
  try {
    const res = await fetch(urlVideoStatistics, {
      headers: { "X-Requested-With": "XMLHttpRequest" }
    });
    if (!res.ok) throw new Error(`Error HTTP ${res.status}`);

    const data = await res.json();
    typeSet = new Set(data.TYPES.map(type => gettext(type.title)));
    disciplineSet = new Set(data.DISCIPLINES.map(discipline => gettext(discipline.title)));
    tagSet = new Set(data.TAGS.map(tag => gettext(tag.title)));

  } catch (err) {
    console.error("Filters cannot be initialized :", err);
  }
}

initFilters();

