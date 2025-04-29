const FILTER_DEFS = [
  // filtre “statique” : liste d’utilisateurs
  {
    type: "static",
    name: "Utilisateur",
    param: "owner",
    searchCallback: getSearchListUsers, // on suppose déjà debounce / memoisé
    itemLabel: u =>
      u.first_name && u.last_name
        ? `${u.first_name} ${u.last_name} (${u.username})`
        : u.username,
    itemKey: u => u.username
  },
  // filtres “API”
  { type: "api", apiKey: "DISCIPLINES", name: "Disciplines", labelProp: "title", valueProp: "slug" },
  { type: "api", apiKey: "TYPES",       name: "Types",       labelProp: "title", valueProp: "slug" },
  { type: "api", apiKey: "TAGS",        name: "Tags",        labelProp: "title", valueProp: "slug" }
];

function debouncePromise(fn, delay = 200) {
  let timer = null;
  let lastReject = null;

  return function(...args) {
    if (timer) {
      clearTimeout(timer);
      lastReject && lastReject({ canceled: true });
    }

    return new Promise((resolve, reject) => {
      lastReject = reject;

      timer = setTimeout(async () => {
        try {
          const result = await fn.apply(this, args);
          resolve(result);
        } catch (err) {
          reject(err);
        } finally {
          timer = null;
          lastReject = null;
        }
      }, delay);
    });
  };
}

function makeSearchInArray(items, labelProp, delay = 200) {
  const searchFn = term => {
    const q = term.trim().toLowerCase();
    if (!q) {
      return Promise.resolve(items);
    }
    const [match, rest] = items.reduce(
      ([m, r], obj) => {
        const txt = String(obj[labelProp]).toLowerCase();
        if (txt.includes(q)) m.push(obj);
        else r.push(obj);
        return [m, r];
      },
      [[], []]
    );
    return Promise.resolve(match.concat(rest));
  };

  return debouncePromise(searchFn, delay);
}

function buildFilterConfig(def, data) {
  if (def.type === "static") {
    return {
      name: def.name,
      param: def.param,
      searchCallback: def.searchCallback,
      itemLabel: def.itemLabel,
      itemKey: def.itemKey
    };
  }

  const items = Array.isArray(data[def.apiKey]) ? data[def.apiKey] : [];
  if (items.length === 0) {
    return null;
  }
  return {
    name: def.name,
    param: def.apiKey.toLowerCase(),
    searchCallback: makeSearchInArray(items, def.labelProp, 200),
    itemLabel: obj => obj[def.labelProp],
    itemKey:   obj => obj[def.valueProp]
  };
}

async function initFilters() {
  try {
    const res = await fetch(urlVideoStatistics, {
      headers: { "X-Requested-With": "XMLHttpRequest" }
    });
    if (!res.ok) throw new Error(`Erreur HTTP ${res.status}`);

    const data = await res.json();

    const filtersConfig = FILTER_DEFS
      .map(def => buildFilterConfig(def, data))
      .filter(Boolean);

    const filterManager = new FilterManager({
      filtersBoxId:    "filtersBox",
      activeFiltersId: "selectedTags",
      resetFiltersId:  "filterTags"
    });

    filtersConfig.forEach(cfg => filterManager.addFilter(cfg));
    filterManager.initializeFilters();
  } catch (err) {
    console.error("Impossible d'initialiser les filtres :", err);
  }
}

initFilters();
