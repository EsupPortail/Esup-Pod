/**
 * Esup-Pod Infinite scroll script
 */

/* exported InfiniteLoader */

/* Read-only Globals defined in utils-playlist.js */
/*
  global preventRefreshButton
*/

// this function (isFooterInView) is not used elsewhere
/*
function isFooterInView() {
  var footer = document.querySelector(
    "footer.container-fluid.pod-footer-container"
  );
  var rect = footer.getBoundingClientRect();
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <=
      (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  );
}
*/
/* Another way to detect the footer
function detect_visibility() {
  var element = document.querySelector(
    "footer.container-fluid.pod-footer-container"
  );

  var top_of_element = element.offsetTop;
  var bottom_of_element =
    element.offsetTop + element.offsetHeight + element.style.marginTop;
  var bottom_of_screen = window.scrollY + window.innerHeight;
  var top_of_screen = window.scrollY;

  if (bottom_of_screen > top_of_element && top_of_screen < bottom_of_element) {
    // Element is visible write your codes here
    // You can add animation or other codes here
    return true;
  } else {
    // the element is not visible, do something else
    return false;
  }
}
*/

/**
 * Checks if a specific footer element is at least 5% visible in the viewport.
 *
 * @function
 * @returns {boolean} Returns true if the footer is visible in the viewport, otherwise false.
 */
const isElementXPercentInViewport = function () {
  const percentVisible = 5;
  var footer = document.querySelector(
    "footer.container-fluid.pod-footer-container",
  );
  let rect = footer.getBoundingClientRect(),
    windowHeight = window.innerHeight || document.documentElement.clientHeight;

  return !(
    Math.floor(100 - ((rect.top >= 0 ? 0 : rect.top) / +-rect.height) * 100) <
      percentVisible ||
    Math.floor(100 - ((rect.bottom - windowHeight) / rect.height) * 100) <
      percentVisible
  );
};

/**
 * InfiniteLoader handles infinite scrolling and dynamic loading of paginated content.
 *
 * @class
 * @param {string} url - The base URL to fetch paginated data from.
 * @param {Function} callBackBeforeLoad - Callback function executed before loading new content.
 * @param {Function} callBackAfterLoad - Callback function executed after new content is loaded.
 * @param {boolean} [nextPage=true] - Indicates if there is a next page to load.
 * @param {number} [page=2] - The initial page number to start loading from.
 *
 * @property {HTMLElement} infinite_loading - The loader element shown during loading.
 * @property {HTMLElement} videos_list - The container element for the loaded content.
 * @property {number} next_page_number - The next page number to load.
 * @property {number} current_page_number - The current page number loaded.
 * @property {boolean|string} nextPage - Indicates if there is a next page to load.
 * @property {Function} callBackBeforeLoad - Callback before loading new content.
 * @property {Function} callBackAfterLoad - Callback after loading new content.
 * @property {string} url - The base URL for fetching data.
 * @property {Function} scroller_init - The scroll event handler for triggering loading.
 *
 * @method initMore - Loads the next page of content and updates the DOM.
 * @method removeLoader - Removes the scroll event listener to stop infinite loading.
 * @method getData - Fetches data for a given page from the server.
 */
class InfiniteLoader {
  constructor(
    url,
    callBackBeforeLoad,
    callBackAfterLoad,
    nextPage = true,
    page = 2,
  ) {
    this.infinite_loading = document.querySelector(".infinite-loading");
    this.videos_list = document.getElementById("videos_list");
    this.next_page_number = page;
    this.current_page_number = page - 1;
    this.nextPage = nextPage;
    this.callBackBeforeLoad = callBackBeforeLoad;
    this.callBackAfterLoad = callBackAfterLoad;
    this.url = url;
    this.scroller_init = () => {
      if (document.body.getBoundingClientRect().top <= this.scrollPos) {
        if (isElementXPercentInViewport()) {
          if (
            this.nextPage &&
            this.next_page_number > this.current_page_number
          ) {
            this.current_page_number = this.next_page_number;
            this.initMore();
          }
        }
      }
      this.scrollPos = document.body.getBoundingClientRect().top;
    };
    window.addEventListener("scroll", this.scroller_init);
  }

  /**
   * Loads the next page of content and updates the DOM.
   */
  async initMore() {
    this.callBackBeforeLoad();
    let url = this.url;
    this.getData(url, this.next_page_number, this.nextPage).then((data) => {
      if (data !== null && data !== undefined) {
        const html = new DOMParser().parseFromString(data, "text/html");
        if (html.getElementById("videos_list").dataset.nextpage !== "True") {
          this.nextPage = false;
        }
        this.nextPage = html.getElementById("videos_list").dataset.nextpage;
        let element = this.videos_list;

        element.innerHTML += html.getElementById("videos_list").innerHTML;
        this.next_page_number += 1;
        const favoritesButtons =
          document.getElementsByClassName("favorite-btn-link");
        for (let btn of favoritesButtons) {
          preventRefreshButton(btn, true);
        }
      }
      this.callBackAfterLoad();
      /* Refresh Bootstrap tooltips after load */
      const tooltipTriggerList = document.querySelectorAll(
        '[data-bs-toggle="tooltip"], [data-pod-tooltip="true"]',
      );
      [...tooltipTriggerList].map(
        (tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl),
      );
      // Hide empty menu
      hideEmptyDropdowns();
    });
  }

  /**
   * Removes the scroll event listener to stop infinite loading.
   */
  removeLoader() {
    window.removeEventListener("scroll", this.scroller_init);
  }

  /**
   * Asynchronously fetches data from a given URL with pagination and CSRF protection.
   *
   * @param {string} url - The base URL to fetch data from.
   * @param {string|number} page - The page identifier or number to append to the URL.
   * @param {string} nextPage - Indicates if there is a next page; if "false", the request is aborted.
   * @returns {Promise<string|undefined>} The response text from the fetch request, or undefined if the request is not made.
   */
  async getData(url, page, nextPage) {
    if (!url) return;
    if (nextPage == "false") return;
    url = url + page;
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "X-CSRFToken": "{{ csrf_token }}",
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "same-origin",
    });
    const data = await response.text();
    return data;
  }
}
