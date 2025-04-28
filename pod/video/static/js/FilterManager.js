/**
 * FilterManager
 *
 * Classe permettant de créer et gérer dynamiquement des filtres interactifs
 * sous forme de dropdowns avec recherche asynchrone, cases à cocher, et affichage
 * des filtres actifs sous forme de badges.
 *
 * Fonctionnalités principales :
 * - Génération automatique d'interfaces de filtre (dropdown + champ de recherche).
 * - Recherche asynchrone sur chaque filtre via des callbacks retournant des Promises.
 * - Gestion des sélections : les éléments sélectionnés sont mis en avant.
 * - Synchronisation avec l'URL (query params) et sessionStorage.
 * - Rafraîchissement automatique de la liste de résultats via `refreshVideosSearch()`.
 *
 * @example
 * // 1. Importer et initialiser
 * import FilterManager from "./FilterManager.js";
 *
 * const manager = new FilterManager({
 *   filtersBoxId: 'filtersBox',
 *   activeFiltersId: 'selectedTags',
 *   resetFiltersId: 'filterTags'
 * });
 *
 * // 2. Définir les filtres à utiliser
 * const filtersConfig = [{
 *   name: 'Disciplines',
 *   param: 'disciplines',
 *   searchCallback: term => searchInSet(mySet, term),
 *   itemLabel: item => item,
 *   itemKey: item => item
 * }];
 *
 * // 3. Ajouter les filtres et initialiser
 * filtersConfig.forEach(cfg => manager.addFilter(cfg));
 * manager.initializeFilters();
 */

class FilterManager {

  /**
   * Ajoute un filtre au manager.
   * @param {Object} options
   * @param {Object} options.filters - Définitions initiales des filtres.
   * @param {string} [options.filtersBoxId='filtersBox'] - ID du container des filtres.
   * @param {string} [options.activeFiltersId='selectedTags'] - ID du container des filtres actifs.
   * @param {string} [options.activeFiltersWrapId='activeFilters'] - ID du container.
   * @param {string} [options.resetFiltersId='filterTags'] - ID du bouton de réinitialisation.
   */
  constructor({
    filters = {},
    filtersBoxId    = 'filtersBox',
    activeFiltersId = 'selectedTags',
    activeFiltersWrapId = 'activeFilters',
    resetFiltersId  = 'filterTags'
  }) {
    this.filters            = filters;
    this.filtersBox         = document.getElementById(filtersBoxId);
    this.activeFiltersBox   = document.getElementById(activeFiltersId);
    this.activeFiltersWrap  = document.getElementById(activeFiltersWrapId);
    this.resetFiltersButton = document.getElementById(resetFiltersId);
    this.initializeResetButton();
    this.currentResults = {};
  }



  /**
   * Ajoute un filtre et génère son composant.
   * @param {string} config.name - Libellé du filtre.
   * @param {string} config.param - Clé de paramètre dans l'URL.
   * @param {Function} config.searchCallback - Fonction de recherche renvoyant une promesse.
   * @param {Function} config.itemLabel - Fonction renvoyant le libellé d'un élément.
   * @param {Function} config.itemKey - Fonction renvoyant la clé unique d'un élément.
   */
  addFilter({ name, param, searchCallback, itemLabel, itemKey }) {
    this.filters[param] = {
      name,
      searchCallback,
      itemLabel,
      itemKey,
      selectedItems: new Map(),
    };
    this.createFilterComponent(name, param);
  }

  /**
   * Génère le DOM du filtre (bouton et liste déroulante).
   * @param {string} name - Libellé du filtre.
   * @param {string} param - Clé de paramètre.
   */
  createFilterComponent(name, param) {
    const dropdown = document.createElement('div');
    dropdown.className = 'dropdown';

    // Bouton du menu déroulant
    const button = document.createElement('button');
    const buttonId = `${param}-filter-btn`;
    button.id = buttonId;
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
    const inputId = `${param}-box`;
    input.placeholder = `Recherche par ${name}`;
    input.id = inputId;
    input.type = 'text';
    input.className = 'form-control';
    inputGroup.appendChild(input);

    const listContainer = document.createElement('div');
    const listContainerId = `collapseFilter${capitalize(param)}`;
    listContainer.className = `form-group navList`;
    listContainer.id = listContainerId;
    listContainer.classList.add('overflow-auto');
    listContainer.style.maxHeight = '200px';

    menu.appendChild(inputGroup);
    menu.appendChild(listContainer);
    dropdown.appendChild(button);
    dropdown.appendChild(menu);
    this.filtersBox.appendChild(dropdown);

    this.addSearchInputListener(param);
  }

  /**
   * Lie les événements de recherche et d'affichage.
   * @param {string} param - Clé de paramètre.
   */
  addSearchInputListener(param) {
    const inputEl  = document.getElementById(`${param}-box`);
    const buttonEl = document.getElementById(`${param}-filter-btn`);
    if (!inputEl || !buttonEl) return;

    inputEl.addEventListener('input', debounce(e => {
      this.searchFilter(param, e.target.value.trim());
    }, 100));

    buttonEl.addEventListener('click', e => {
      e.preventDefault();
      this.searchFilter(param, '');
    });
  }

  /**
   * Lance la recherche via la callback et met à jour l'affichage.
   * @param {string} param - Clé de paramètre.
   * @param {string} [searchTerm=''] - Terme de recherche.
   */
  async searchFilter(param, searchTerm = '') {
    const filter = this.filters[param];
    if (!filter || typeof filter.searchCallback !== 'function') return;

    try {
      const results = await filter.searchCallback(searchTerm);
      this.currentResults[param] = results;
      this.createCheckboxesForFilter(param, results);
    } catch (err) {
      console.error(err);
    }
  }


  /**
   * Supprime un filtre appliqué.
   * @param {string} param - Le paramètre du filtre.
   */
  removeFilter(currentFilter, key) {
    if (currentFilter) {
      currentFilter.selectedItems.delete(key);
      document.getElementById(`${slugify(key)}-tag`).remove();
      sessionStorage.setItem(`filter-${currentFilter.param}`, JSON.stringify(Array.from(currentFilter.selectedItems.keys())));
      this.update();
    }
  }

  /**
   * Initialise les filtres depuis la session.
   */
  initializeFilters() {
    Object.keys(this.filters).forEach(param => {
      const filter = this.filters[param];
      const selectedItems = JSON.parse(sessionStorage.getItem(`filter-${param}`)) || [];
      selectedItems.forEach(item => {
        filter.selectedItems.set(item, true);
        this.renderActiveFilter(filter, item);
      });
    });
    this.update();
  }

  /**
   * Affiche un badge pour chaque filtre actif.
   * @param {Object} filter - Objet de configuration du filtre.
   * @param {string} key - Clé de l'élément sélectionné.
   */
  renderActiveFilter(currentFilter, key) {
    if (currentFilter) {
      const container = this.activeFiltersBox;

      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'user-btn user-btn--large';
      button.id = `${slugify(key)}-tag`;

      const label = document.createElement('span');
      label.innerText = key;

      const closeIcon = document.createElement('span');
      closeIcon.className = 'bi bi-x-lg';
      closeIcon.style.marginLeft = '0.5rem';
      closeIcon.setAttribute('aria-label', 'Remove Filter');
      closeIcon.addEventListener('click', () => {
        this.removeFilter(currentFilter, key);
      });

      button.appendChild(label);
      button.appendChild(closeIcon);
      container.appendChild(button);
    }
  }

  /**
   * Construit et insère les cases à cocher en optimisant avec DocumentFragment.
   * @param {string} param - Clé de paramètre.
   * @param {Array} results - Résultats de recherche.
   */
  createCheckboxesForFilter(param, results) {
    const container = document.getElementById(`collapseFilter${capitalize(param)}`);
    container.innerHTML = '';
    const filter = this.filters[param];
    const fragment = document.createDocumentFragment();

    filter.selectedItems.forEach((_, key) => {
      const formCheck = document.createElement('div');
      formCheck.className = 'form-check mb-2';

      const checkbox = document.createElement('input');
      checkbox.className = 'form-check-input';
      checkbox.type      = 'checkbox';
      checkbox.id        = key;
      checkbox.checked   = true;

      checkbox.addEventListener('change', () => {
        if (checkbox.checked) {
          filter.selectedItems.set(key, true);
          this.renderActiveFilter(filter, key);
        } else {
          filter.selectedItems.delete(key);
          this.removeFilter(filter, key);
        }
        this.update();
        this.createCheckboxesForFilter(param, this.currentResults[param] || []);
      });

      const label = document.createElement('label');
      label.className = 'form-check-label';
      label.setAttribute('for', key);
      const matching = (this.currentResults[param] || [])
                        .find(r => slugify(filter.itemKey(r)) === key);
      label.innerText = matching ? filter.itemLabel(matching) : key;

      formCheck.append(checkbox, label);
      fragment.appendChild(formCheck);
    });

    results.forEach(res => {
      const temp = filter.itemKey(res);
      const key  = slugify(temp);
      if (filter.selectedItems.has(key)) return;

      const formCheck = document.createElement('div');
      formCheck.className = 'form-check mb-2';

      const checkbox = document.createElement('input');
      checkbox.className = 'form-check-input';
      checkbox.type      = 'checkbox';
      checkbox.id        = key;
      checkbox.checked   = false;

      checkbox.addEventListener('change', () => {
        if (checkbox.checked) {
          filter.selectedItems.set(key, true);
          this.renderActiveFilter(filter, key);
        } else {
          filter.selectedItems.delete(key);
          this.removeFilter(filter, key);
        }
        this.update();
        this.createCheckboxesForFilter(param, this.currentResults[param] || []);
      });

      const label = document.createElement('label');
      label.className = 'form-check-label';
      label.setAttribute('for', key);
      label.innerText = filter.itemLabel(res);

      formCheck.append(checkbox, label);
      fragment.appendChild(formCheck);
    });

    container.appendChild(fragment);
  }


  /**
   * Met à jour la sessionStorage et l'URL avec les filtres sélectionnés.
   */
  update() {
    const query = new URLSearchParams();

    Object.keys(this.filters).forEach(param => {
      const filter = this.filters[param];
      const selectedKeys = Array.from(filter.selectedItems.keys());
      if (selectedKeys.length > 0) {
        query.set(param, selectedKeys.join(','));
        sessionStorage.setItem(`filter-${param}`, JSON.stringify(selectedKeys));
      } else {
        query.delete(param);
        sessionStorage.removeItem(`filter-${param}`);
      }
    });
    const newUrl = `${window.location.pathname}?${query.toString()}`;
    window.history.replaceState(null, '', newUrl);
    this._syncResetLink();
    refreshVideosSearch();
  }

   /**
   * Positionne le lien "Effacer les filtres" :
   * - dans filtersBox s'il n'y a aucun tag actif
   * - dans activeFiltersWrap (à droite) sinon
   */
   _syncResetLink() {
    const hasTags = this.activeFiltersBox.children.length > 0;

    if (!hasTags) {
      // aucun filtre actif → lien dans filtersBox
      if (!this.filtersBox.contains(this.resetFiltersButton)) {
        this.filtersBox.appendChild(this.resetFiltersButton);
      }
      this.resetFiltersButton.classList.add('ms-auto');
      this.filtersBox.classList.remove('mb-3');
    } else {
      if (!this.activeFiltersWrap.contains(this.resetFiltersButton)) {
        this.activeFiltersWrap.appendChild(this.resetFiltersButton);
      }
      this.resetFiltersButton.classList.add('ms-auto');
      this.filtersBox.classList.add('mb-3');
    }
    this.resetFiltersButton.style.display = 'block';
  }


  /**
   * Supprime tous les tags affichés en tant que filtres actifs.
   */
  removeAllActiveFiltersUI() {
    this.activeFiltersBox.querySelectorAll('span.badge').forEach(badge => badge.remove());
  }

  /**
   * Supprime un filtre actif et rafraîchit.
   * @param {Object} filter - Objet de configuration du filtre.
   * @param {string} key - Clé de l'élément à retirer.
   */
  resetFilters() {
    Object.values(this.filters).forEach(filter => {
      Array.from(filter.selectedItems.keys()).forEach(key => {
        this.removeFilter(filter, key);
      });
    });
    this.removeAllActiveFiltersUI();
  }

  /**
   * Initialisation du bouton de réinitialisation des filtres.
   */
  initializeResetButton() {
    if (this.resetFiltersButton) {
      this.resetFiltersButton.addEventListener('click', (e) => {
        e.preventDefault();
        this.resetFilters(); // Réinitialiser les filtres
      });
    }
  }
}

/**
 * Convertit une chaîne en slug utilisable dans un ID.
 * @param {string} str
 * @returns {string}
 */
function slugify(nom) {
  return String(nom)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/\s+/g, '')
    .replace(/[^a-z0-9]/g, '');
}

/**
 * Met la première lettre en majuscule.
 * @param {string} s
 * @returns {string}
 */
function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Applique un délai avant d'exécuter la fonction.
 * @param {Function} fn
 * @param {number} delay
 * @returns {Function}
 */
function debounce(fn, delay = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}
