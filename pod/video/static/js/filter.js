// Filtes
let typeSet = new Set();
let disciplineSet = new Set();
let tagSet = new Set();

const filtersConfig = [
  {
    name: "Utilisateur",
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


/* Fonction qui simule un fetch via un Set */
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
  console.log("COUCOU");
  try {
    const res = await fetch(urlVideoStatistics, {
      headers: { "X-Requested-With": "XMLHttpRequest" }
    });
    if (!res.ok) throw new Error(`Erreur HTTP ${res.status}`);

    const data = await res.json();
    help(data);
    typeSet = new Set(data.TYPES.map(type => type.title));
    disciplineSet = new Set(data.DISCIPLINES.map(discipline => discipline.title));
    tagSet = new Set(data.TAGS.map(tag => tag.title));

  } catch (err) {
    console.error("Impossible d'initialiser les filtres :", err);
  }
}

initFilters();

function help(data) {
  console.log(data);
  data.TYPES.forEach(type => {
    console.log(type.title);
  });
  console.log(data.DISCIPLINES);
  console.log(data.VIDEOS_COUNT);
  console.log(data.VIDEOS_DURATION);
  console.log(data.CHANNELS_PER_BATCH);
  console.log(data.TAGS);
}
