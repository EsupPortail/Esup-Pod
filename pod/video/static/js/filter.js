// Liste simulant les catégories
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
    name: "Disciplines",
    param: "disciplines",
    searchCallback: term => searchInSet(categorySet, term),
    itemLabel: category => category,
    itemKey: category => category,
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