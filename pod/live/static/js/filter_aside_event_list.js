let loader = document.querySelector(".lds-ring");
let checkedInputs = [];

/**
 * Enable /disable all checkboxes.
 *
 * @param {boolean} value
 */
function disableCheckboxes(value) {
  document.querySelectorAll("input[type=checkbox]").forEach((checkbox) => {
    checkbox.disabled = value;
  });
}

/**
 * Return url with filters params.
 *
 * @returns {string}
 */
function getUrlForRefresh() {
  let newUrl = window.location.pathname + "?";

  checkedInputs.forEach((input) => {
    newUrl += input.name + "=" + input.value + "&";
  });

  // Add page parameter
  newUrl += "page=1";
  return newUrl;
}

/**
 * Remove loader height.
 *
 * @param height
 * @returns {number}
 */
function getHeightMinusLoader(height) {
  let loader_style = getComputedStyle(loader);
  let loader_height = loader_style.height;
  loader_height = loader_height.replace("px", "");
  return height - loader_height;
}

/**
 * Async request to refresh view with filtered events list.
 */
function refreshEvents() {
  // Erase list and enable loader
  const events_content = document.getElementById("events_content");
  let width = events_content.offsetWidth;
  let height = getHeightMinusLoader(events_content.offsetHeight);

  events_content.innerHTML =
    "<div style='height: " + height + "px; width:" + width + "px'></div>";
  loader.classList.add("show");

  let url = getUrlForRefresh();

  // Async GET request wth parameters by fetch method
  fetch(url, {
    method: "GET",
    headers: {
      "X-CSRFToken": "{{ csrf_token }}",
      "X-Requested-With": "XMLHttpRequest",
    },
    cache: "no-store",
  })
    .then((response) => response.text())
    .then((data) => {
      // parse data into html and replace videos list
      let parser = new DOMParser();
      let html = parser.parseFromString(data, "text/html").body;
      events_content.outerHTML = html.innerHTML;

      // change url with params sent
      window.history.pushState({}, "", url);
    })
    .catch(() => {
      events_content.innerHTML = gettext("An Error occurred while processing.");
    })
    .finally(() => {
      // Re-enable inputs and dismiss loader
      disableCheckboxes(false);
      loader.classList.remove("show");
    });
}

/**
 * Check or uncheck checkbox regarding url params.
 *
 * @param el
 */
function setCheckboxStatus(el) {
  let currentUrl = window.location.href;
  el.checked = currentUrl.includes("type=" + el.value + "&");
}

/**
 * Add listener to refresh events list on checkbox status change.
 *
 * @param el
 */
function addCheckboxListener(el) {
  el.addEventListener("change", () => {
    checkedInputs = [];
    disableCheckboxes(true);
    document
      .querySelectorAll("#collapseFilterType input[type=checkbox]:checked")
      .forEach((e) => {
        checkedInputs.push(e);
      });
    refreshEvents();
  });
}

// On page load
document
  .querySelectorAll("#collapseFilterType input[type=checkbox]")
  .forEach((el) => {
    setCheckboxStatus(el);
    addCheckboxListener(el);
  });
