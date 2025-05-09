/**
 * FilterManager
 *
 * Class for dynamically creating and managing interactive filters
 * in the form of dropdowns with asynchronous search, checkboxes,
 * and active filter display as badges.
 *
 * Main features:
 * - Automatic generation of filter interfaces (dropdown + search field).
 * - Asynchronous search for each filter using callbacks returning Promises.
 * - Selection management: selected items are highlighted.
 * - Synchronization with the URL (query params) and sessionStorage.
 * - Automatic refresh of the results list via `refreshVideosSearch()`.
 *
 * @example
 * // 1. Import and initialize
 * import FilterManager from "./FilterManager.js";
 *
 * const manager = new FilterManager({
 *   filtersBoxId: 'filtersBox',
 *   activeFiltersId: 'selectedTags',
 *   resetFiltersId: 'filterTags'
 * });
 *
 * // 2. Define the filters to use
 * const filtersConfig = [{
 *   name: 'Disciplines',
 *   param: 'disciplines',
 *   searchCallback: term => searchInSet(mySet, term),
 *   itemLabel: item => item,
 *   itemKey: item => item
 * }];
 *
 * // 3. Add the filters and initialize
 * filtersConfig.forEach(cfg => manager.addFilter(cfg));
 * manager.initializeFilters();
 */
class FilterManager {

  /**
   * Adds a filter to the manager.
   * @param {Object} options
   * @param {Object} options.filters - Initial filter definitions.
   * @param {string} [options.filtersBoxId='filtersBox'] - ID of the filters container.
   * @param {string} [options.activeFiltersId='selectedTags'] - ID of the active filters container.
   * @param {string} [options.activeFiltersWrapId='activeFilters'] - ID of the wrapper container.
   * @param {string} [options.resetFiltersId='filterTags'] - ID of the reset button.
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
   * Adds a filter and generates its component.
   * @param {string} config.name - Label of the filter.
   * @param {string} config.param - Parameter key used in the URL.
   * @param {Function} config.searchCallback - Search function that returns a promise.
   * @param {Function} config.itemLabel - Function that returns the label of an item.
   * @param {Function} config.itemKey - Function that returns the unique key of an item.
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
   * Generates the DOM structure for the filter (button and dropdown list).
   * @param {string} name - Label of the filter.
   * @param {string} param - Parameter key.
   */
  createFilterComponent(name, param) {
    const dropdown = document.createElement('div');
    dropdown.className = 'dropdown';

    // Dropdown menu button
    const button = document.createElement('button');
    const buttonId = `${param}-filter-btn`;
    button.id = buttonId;
    button.className = 'btn btn-outline-primary dropdown-toggle';
    button.type = 'button';
    button.setAttribute('data-bs-toggle', 'dropdown');
    button.setAttribute('aria-expanded', 'false');
    button.setAttribute('aria-label', gettext(`Show or hide filter options for ${name}`));
    button.innerText = name;

    // Dropdown menu
    const menu = document.createElement('div');
    menu.className = 'dropdown-menu p-2';
    menu.style.minWidth = '17em';

    // Search group (input)
    const inputGroup = document.createElement('div');
    inputGroup.className = 'input-group mb-3';

    const input = document.createElement('input');
    const inputId = `${param}-box`;
    input.placeholder = gettext('Search for a') +" "+ name;
    input.setAttribute('aria-label', gettext('Search for a') +" "+ name);
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
    listContainer.setAttribute('aria-label', gettext(`Filter option for`) +" "+ name);

    menu.appendChild(inputGroup);
    menu.appendChild(listContainer);
    dropdown.appendChild(button);
    dropdown.appendChild(menu);
    this.filtersBox.appendChild(dropdown);

    this.addSearchInputListener(param);
  }

  /**
   * Binds search and display events.
   * @param {string} param - Parameter key.
   */
  addSearchInputListener(param) {
    const inputEl  = document.getElementById(`${param}-box`);
    const buttonEl = document.getElementById(`${param}-filter-btn`);
    if (!inputEl || !buttonEl) return;

    inputEl.addEventListener('input', debounce(e => {
      e.preventDefault();
      this.searchFilter(param, e.target.value.trim());
    }, 100));

    buttonEl.addEventListener('click', e => {
      e.preventDefault();
      this.searchFilter(param, '');
    });
  }

  /**
   * Initiates the search via the callback and updates the display.
   * @param {string} param - Parameter key.
   * @param {string} [searchTerm=''] - Search term.
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
   * Removes an applied filter.
   * @param {string} param - The filter parameter.
   */
  removeFilter(currentFilter, key) {
    if (currentFilter) {
      const filterElement = document.getElementById(`${slugify(key)}-tag`);
      const closeButton = document.getElementById(`remove-filter-${slugify(key)}`);
      if (closeButton) {
        const tooltip = bootstrap.Tooltip.getInstance(closeButton);
        if (tooltip) tooltip.dispose();
      }
      if (filterElement) filterElement.remove();
      currentFilter.selectedItems.delete(key);
      sessionStorage.setItem(`filter-${currentFilter.param}`, JSON.stringify(Array.from(currentFilter.selectedItems.keys())));
      this.update();
    }
  }


  /**
   * Initializes the filters from the session.
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
   * Displays a badge for each active filter.
   * @param {Object} filter - Filter configuration object.
   * @param {string} key - Key of the selected item.
   */
  renderActiveFilter(currentFilter, key) {
    if (currentFilter) {
      const container = this.activeFiltersBox;
      const filterContainer = document.createElement('div');
      filterContainer.className = 'btn btn-secondary align-items-center d-flex';
      filterContainer.id = `${slugify(key)}-tag`;
      filterContainer.setAttribute('role', 'button');
      filterContainer.setAttribute('tabindex', '0');
      filterContainer.setAttribute('aria-label', `${currentFilter.name}: ${key}`);
      const label = document.createElement('span');
      label.innerText = `${currentFilter.name}: ${key}`;
      const closeButton = document.createElement('button');
      closeButton.type = 'button';
      closeButton.className = 'btn-close';
      closeButton.style.marginLeft = '0.5rem';
      closeButton.id = `remove-filter-${slugify(key)}`;
      closeButton.setAttribute('data-bs-toggle', 'tooltip');
      closeButton.setAttribute('data-bs-placement', 'top');
      closeButton.setAttribute('title', 'Remove filter');
      closeButton.setAttribute('aria-label', `Click to remove the filter: ${currentFilter.name} - ${key}`);
      closeButton.addEventListener('click', (e) => {
        e.preventDefault();
        this.removeFilter(currentFilter, key);
      });
      closeButton.addEventListener('keydown', (e) => {
        e.preventDefault();
        if (e.key === 'Enter' || e.key === ' ') {
          this.removeFilter(currentFilter, key);
        }
      });
      filterContainer.appendChild(label);
      filterContainer.appendChild(closeButton);
      container.appendChild(filterContainer);
      new bootstrap.Tooltip(closeButton);
    }
  }

  /**
   * Builds and inserts the checkboxes, optimized with DocumentFragment.
   * @param {string} param - Parameter key.
   * @param {Array} results - Search results.
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
      checkbox.type = 'checkbox';
      checkbox.id = key;
      checkbox.checked = true;

      checkbox.addEventListener('change', (e) => {
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

      checkbox.addEventListener('change', (e) => {
        e.preventDefault();
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
   * Updates the sessionStorage and URL with the selected filters.
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
    selectAllManger(); // Fonction appeller dans videoSelect
  }

  /**
  * Positions the "Clear filters" link:
  * - in activeFiltersWrap (on the right) otherwise
  */
  _syncResetLink() {
    const hasTags = this.activeFiltersBox.children.length > 0;

    if (!hasTags) {
      this.filtersBox.classList.remove('mb-3');
      this.resetFiltersButton.style.display = 'none';
      return;
    }

    if (!this.activeFiltersWrap.contains(this.resetFiltersButton)) {
      this.activeFiltersWrap.appendChild(this.resetFiltersButton);
    }
    this.resetFiltersButton.classList.add('ms-auto');
    this.filtersBox.classList.add('mb-3');
    this.resetFiltersButton.style.display = 'block';
  }



  /**
   * Removes all tags displayed as active filters.
   */
  removeAllActiveFiltersUI() {
    this.activeFiltersBox.querySelectorAll('span.badge').forEach(badge => badge.remove());
  }

  /**
   * Removes an active filter and refreshes.
   * @param {Object} filter - Filter configuration object.
   * @param {string} key - Key of the item to remove.
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
   * Initialization of the filter reset button.
   */
  initializeResetButton() {
    if (this.resetFiltersButton) {
      this.resetFiltersButton.addEventListener('click', (e) => {
        e.preventDefault();
        this.resetFilters();
      });
    }
  }
}

/**
 * Converts a string into a slug usable in an ID.
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
 * Capitalizes the first letter of a string.
 * @param {string} s
 * @returns {string}
 */
function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Applies a delay before executing the function.
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
