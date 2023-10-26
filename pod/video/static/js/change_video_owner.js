(function () {
  const base = window.location.origin;
  const update_videos_url = `${base}/video/updateowner/put/`;
  const get_videos_url = `${base}/video/updateowner/videos/`;
  const get_owners_url = `${base}/video/updateowner/owners/`;

  const old_owner_input = document.querySelector("#oldlogin");
  const new_owner_input = document.querySelector("#newlogin");
  const suggestions = [
    document.querySelector(".oldlogin.suggestions"),
    document.querySelector(".newlogin.suggestions"),
  ];
  const list_videos__search = document.querySelector("#list_videos__search");
  const videos_container = document.querySelector(
    ".form-wrapper__control.select-videos",
  );
  const next_content = document.querySelector(".paginator #next_content");
  const pages_info = document.querySelector(".paginator #pages_infos");
  const previous_content = document.querySelector(
    ".paginator #previous_content",
  );

  const submitBTN = document.querySelector("#submitChanges");

  const selectAllVideos = document.getElementById("select_all");

  let new_username_id = null;

  let filtered_word = undefined;

  const limit = 12;
  const offset = 0;

  // Save choosed videos
  let choosed_videos = [];

  // reload video after trying filter
  let previous_videos_url = null;
  let can_filter = false;

  let current_username_filter = null;
  let current_username_id = null;
  let DATA = { count: 0, next: null, previous: null, results: [] };

  /**
   * Select all videos
   */
  const checkAllVideos = () => {
    selectAllVideos.addEventListener("change", () => {
      const videosCards =
        videos_container.querySelectorAll(".card.manage_video");
      if (selectAllVideos.checked && !!DATA.results.length) {
        // select all videos
        videosCards.forEach((videoCard) => {
          if (!videoCard.classList.contains("choosed")) videoCard.click();
        });
      } else if (!selectAllVideos.checked && !!DATA.results.length) {
        // Unselect all videos
        videosCards.forEach((videoCard) => {
          if (videoCard.classList.contains("choosed")) videoCard.click();
        });
      }
    });
  };

  // Apply listener on selectAllVideos/UnselectAllVideos checkbox
  checkAllVideos();

  /**
   * Show alert message
   */
  class AlertMessage extends HTMLElement {
    constructor(message, alert_class = "success") {
      super();
      let html = document.createElement("DIV");
      html.setAttribute("class", "alert " + `alert-${alert_class}`);
      let content = document.createElement("DIV");
      content.setAttribute("class", "alert_message");
      content.innerText = message || alert_class;
      html.appendChild(content);
      this.appendChild(html);
    }
    connectedCallback() {
      super.connectedCallback && super.connectedCallback();
      window.setTimeout(() => {
        this.classList.add("alert_close");
        window.setTimeout(() => {
          this.parentElement.removeChild(this);
        }, 1000);
      }, 3000);
    }
  }
  customElements.define("alert-message", AlertMessage);

  /**
   * Add not found text
   * @param {HTMLElement} container
   * @param {Boolean} clickable if true, text can be remove by a click on it
   */
  const addNotFound = (container, clickable = false) => {
    const div = document.createElement("DIV");
    div.setAttribute("class", "alert-warning text-center full-width");
    div.innerText = gettext("No element found");
    if (clickable)
      div.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        div.remove();
      });
    container.innerHTML = "";
    container.appendChild(div);
  };

  /**
   * Add or remove loader
   * @param {HTMLElement} container
   * @param {Boolean} remove if true, try to remove loader
   */
  const addRemoveLoader = (container = null, remove = false) => {
    let loader = document.querySelector(".manage-video__loader");
    if (!loader) {
      loader = document.createElement("div");
      loader.setAttribute("class", "manage-video__loader text-center");
      loader.innerHTML = `<div class="spinner-border text-primary" role="status"><span class="visually-hidden">${gettext(
        "Loading…",
      )}</span></div>`;
    }
    if (remove) loader.remove();
    else if (!container.querySelector(".spinner-border") && !remove) {
      container.innerHTML = "";
      container.appendChild(loader);
    }
  };

  /**
   * Add element in list
   * @param {Number} el
   * @param {Array} list where to add element
   */
  const addInChoosedVideosArray = (el) => {
    if (choosed_videos.includes(el))
      choosed_videos = choosed_videos.filter((e) => e !== el);
    else choosed_videos = [...choosed_videos, el];
  };

  /**
   *
   * @param {HTMLInputElement} input field
   * @param {Number} user_id user ID
   */
  const setOwner = (input, user_id) => {
    if (input.id.includes("newlogin")) new_username_id = user_id;
  };

  /**
   * return GET param from url
   * @param {String} url
   * @param {String} param key name
   * @param {defaultValue} default value if not found
   * @return {String} value found or default value
   */
  const getSearchParamFromURL = (url, key, defaultValue = null) => {
    const data = new URL(url).search
      .toLowerCase()
      .replace("?", "")
      .split("&")
      .filter((el) => el.includes(key.toLowerCase()));
    if (data.length >= 1 && data[0].includes("=")) {
      const arr = data[0].split("=");
      return arr.length >= 2 ? arr[1] : defaultValue;
    }
    return defaultValue;
  };

  /**
   * Refresh info current page 0/0
   * @param {String} url
   */
  const refreshPageInfos = (url = null) => {
    let text = "0/0";
    if (url === null) {
      pages_info.innerText = text;
      return;
    }
    const curr_offset = Number.parseInt(
      getSearchParamFromURL(url, "offset", 0),
    );
    const curr_page = curr_offset === 0 ? 1 : 1 + curr_offset / limit;
    const total_page = Math.ceil(DATA.count / limit);
    text = `${curr_page}/${total_page}`;
    pages_info.innerText = text;
  };

  /**
   * Listener to pagination next page
   * @param {ClickEvent} e emitted event
   */
  const nextPreviousHandler = function (e) {
    e.preventDefault();
    e.stopPropagation();
    selectAllVideos.checked = false;
    if (this.isEqualNode(previous_content)) {
      if (!!DATA.previous && current_username_id) {
        addRemoveLoader(videos_container);
        prev_url = DATA.previous;
        if (filtered_word !== undefined) prev_url += `&q=${filtered_word}`;
        getVideos(prev_url, (data) => {
          addRemoveLoader(null, true);
          if (data.results.length === 0) {
            addNotFound(videos_container);
            return;
          }
          DATA = { ...data };
          refreshVideos(`${base}${prev_url}`, data.results);
        });
      }
    } else {
      if (!!DATA.next && current_username_id) {
        addRemoveLoader(videos_container);
        next_url = DATA.next;
        if (filtered_word !== undefined) next_url += `&q=${filtered_word}`;
        getVideos(next_url, (data) => {
          addRemoveLoader(null, true);
          if (data.results.length === 0) {
            addNotFound(videos_container);
            return;
          }
          DATA = { ...data };
          refreshVideos(`${base}${next_url}`, data.results);
        });
      }
    }
  };

  /**
   * Refresh pagination Listener
   */
  const refreshPagination = () => {
    next_content.classList.toggle("disabled", !DATA.next);
    previous_content.classList.toggle("disabled", !DATA.previous);

    next_content.removeEventListener("click", nextPreviousHandler);
    previous_content.removeEventListener("click", nextPreviousHandler);

    next_content.addEventListener("click", nextPreviousHandler);
    previous_content.addEventListener("click", nextPreviousHandler);
  };

  /**
   * Clear suggestion elements
   * @param {HTMLElement} suggestion suggestion container
   */
  const clearSuggestions = (suggestion) => {
    suggestion.innerHTML = "";
  };

  /**
   * Make request to url
   * @param {String} url request url
   * @param {String} method request method
   * @param {FormData} body post data
   * @returns {Promise} response
   */
  const makeRequest = (
    url,
    method = "GET",
    body = new FormData(),
    csrf = null,
  ) => {
    let data = {
      method,
    };
    if (csrf) data = { ...data, headers: { "X-CSRFToken": csrf } };
    if (method.toLowerCase() === "post") data["body"] = body;
    return fetch(url, data).then((data) => {
      return data.json().then((response) => {
        return response;
      });
    });
  };

  /**
   * Add search event to an input element with delay before user stops writing
   * @param {HTMLInputElement} input field to add listener
   * @param {Function} callback event action
   * @param {Number} delay wait time after user stops writing before executing callback
   */
  const addSearchListener = (input, callback, delay = 1100) => {
    let timer = null;
    let once = false;
    input.addEventListener("keyup", (e) => {
      if (
        (/[a-z0-9\s]/.test(e.key.toLowerCase()) && e.key.length == 1) ||
        e.key.toLowerCase() == "backspace"
      ) {
        const is_filter_input = input.isEqualNode(list_videos__search);
        const valid_input = input.value.trim().length >= 3;
        const loader_exists = !!document.querySelector(".manage-video__loader");
        // show loader on filter field only if DATA.results is not empty
        if (is_filter_input && !!DATA.results.length) {
          addRemoveLoader(input.nextElementSibling);
          if (
            !valid_input &&
            !loader_exists &&
            videos_container.childElementCount === 0
          ) {
            // show loader
            addRemoveLoader(videos_container);
          }
        } else if (valid_input && !is_filter_input)
          addRemoveLoader(input.nextElementSibling);
        if (!valid_input) {
          clearSuggestions(input.nextElementSibling);
        }

        once = true;
        timer = window.setTimeout(() => {
          if (once && !!timer) {
            callback(input);
          }
          once = false;
          clearTimeout(timer);
          timer = null;
        }, delay);
      }
    });

    input.addEventListener("keydown", () => {
      once = false;
      clearTimeout(timer);
      timer = null;
    });
  };

  /**
   * Add click event on user suggestion to get some of his videos
   * @param {HTMLParagraphElement} p element to add listener
   * @param {Number} user_id
   * @param {HTMLInputElement} input field to set value with user fullname
   */
  const addGetVideosListener = (p, user_id, input, ..._) => {
    p.addEventListener("click", (e) => {
      e.preventDefault();
      current_username_filter = e.target.textContent.trim().toLowerCase();
      if (input.id.includes("oldlogin")) {
        const old_user_id = current_username_id;
        current_username_id = user_id;
        if (old_user_id !== current_username_id) choosed_videos = [];
      }
      setOwner(input, user_id);

      input.value = current_username_filter;
      clearSuggestions(input.nextElementSibling);
      if (input.id.includes("oldlogin")) {
        const url = `${get_videos_url}${current_username_id}?limit=${limit}&offset=${offset}`;
        getVideos(url, (data) => {
          DATA = data;
          if (!!!data.results.length) {
            addNotFound(videos_container);
            return;
          }
          // refresh video container
          refreshVideos(url);
        });
      }
    });
  };

  /**
   * Filter videos by title
   * @param {HTMLParagraphElement} p suggestion user
   * @param {Any} _ Not use
   * @param {HTMLInputElement} input field
   * @param {String} text input value
   * @param {String} url current url
   */
  const filterVideosListener = (p, _, input, text, url) => {
    p.addEventListener("click", (e) => {
      const title = text || p.textContent.trim().toLowerCase();
      e.preventDefault();
      refreshVideos(
        `${base}${url}`,
        DATA.results.filter((video) =>
          video.title.toLowerCase().includes(title),
        ),
      );
      clearSuggestions(input.nextElementSibling);
    });
  };

  /**
   * Get users from the server
   * @param {String} search
   * @returns {Promise} users found
   */
  const getUsers = (search) => {
    const url = `${get_owners_url}?q=${search}&limit=${limit}&offset=${offset}`;
    return makeRequest(url);
  };

  /**
   * Make request from server to get videos
   * @param {String} url current url
   * @param {Callable} callback callback after request
   * @param {Boolean} is_filter is filter input
   * @returns
   */
  const getVideos = (url, callback, is_filter = false) => {
    return makeRequest(url).then((data) => {
      if (!is_filter) {
        previous_videos_url = url;
        can_filter = !!data.results.length;
      }
      return callback(data);
    });
  };

  /**
   * Refresh videos to show
   * @param {String} url request url
   * @param {Array} videos list of videos
   */
  const refreshVideos = (url, videos = DATA.results) => {
    videos_container.innerHTML = "";
    videos.forEach((video) => {
      const cls = choosed_videos.includes(video.id) ? "choosed" : "";
      const card = document.createElement("DIV");
      card.setAttribute("class", `card manage_video ${cls}`);
      card.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        card.classList.toggle("choosed");
        addInChoosedVideosArray(video.id);
      });

      const body = document.createElement("DIV");
      body.setAttribute("class", "body");

      const footer = document.createElement("DIV");
      footer.setAttribute("class", "footer");

      const title = document.createElement("SPAN");
      title.setAttribute("class", "video-title");
      title.setAttribute("title", video.title);
      title.innerText = video.title;

      img = document.createElement("img");
      img.setAttribute("src", video.thumbnail);
      img.setAttribute("alt", video.title);
      body.appendChild(img);
      footer.appendChild(title);
      card.appendChild(body);
      card.appendChild(footer);
      videos_container.appendChild(card);
    });
    refreshPagination();
    refreshPageInfos(url);
  };

  /**
   *
   * @param {String} text user first_name & last_name
   * @param {Number} id user id
   * @param {HTMLInputElement} input field
   * @param {String} cls css class
   * @param {Callable} listenerCallback callback on click
   * @param {String} url current url
   */
  const addSuggestionElement = (
    text,
    id,
    input,
    cls,
    listenerCallback,
    url = null,
  ) => {
    // add current search as option
    if (!input.nextElementSibling.querySelector("#current_search") && url) {
      const search_text = input.value.trim();
      const search = document.createElement("P");
      search.setAttribute("id", "current_search");
      search.innerText = `Recherche "${search_text}"`;
      listenerCallback(search, id, input, search_text, url);
      input.nextElementSibling.appendChild(search);
    }
    p = document.createElement("P");
    p.setAttribute("class", cls);
    p.innerText = `${text}`;
    listenerCallback(p, id, input, null, url);
    input.nextElementSibling.appendChild(p);
  };

  /**
   * Add to suggestion div some found users by input value
   * @param {HTMLInputElement} input
   */
  const proposeUsers = (input) => {
    const username = input.value.trim().toLowerCase();
    if (username.length >= 3) {
      getUsers(username).then((users) => {
        clearSuggestions(input.nextElementSibling);
        if (!!!users.length) addNotFound(input.nextElementSibling, true);
        users.forEach((user) => {
          addSuggestionElement(
            `${user.first_name} ${user.last_name}`,
            user.id,
            input,
            "user_item",
            addGetVideosListener,
          );
        });
      });
    }
    clearSuggestions(input.nextElementSibling);
    if (
      current_username_filter !== username &&
      input.isEqualNode(old_owner_input)
    ) {
      videos_container.innerHTML = "";
      reset(true);
    }
  };

  /**
   * Adding search listener to filter input
   */
  addSearchListener(list_videos__search, (input) => {
    const search = input.value.trim().toLowerCase();
    if (!!current_username_id && can_filter && search.length >= 3) {
      filtered_word = search;
      const url = `${get_videos_url}${current_username_id}?limit=${limit}&offset=${offset}&title=${search}`;
      getVideos(
        url,
        (data) => {
          DATA = { ...data };
          if (!!!data.results.length) {
            addNotFound(list_videos__search.nextElementSibling, true);
          } else {
            // Remove loader
            addRemoveLoader(null, true);
          }

          data.results.forEach((video) => {
            addSuggestionElement(
              `${video.title}`,
              video.id,
              input,
              "user_item",
              filterVideosListener,
              url,
            );
          });
        },
        true,
      );
    } else if (
      !!previous_videos_url &&
      !!current_username_id &&
      search.length < 3
    ) {
      getVideos(previous_videos_url, (data) => {
        DATA = { ...data };
        refreshVideos(`${base}${previous_videos_url}`, data.results);
      });
      filtered_word = undefined;
    }
  });

  /**
   * Adding search Listener to owner inputs
   */
  [old_owner_input, new_owner_input].forEach((input) => {
    addSearchListener(input, proposeUsers);
  });

  /**
   * Adding click event on user suggestions
   */
  suggestions.forEach((suggestion) => {
    suggestion.addEventListener("click", (e) => {
      suggestion.previousElementSibling.value = e.target.textContent;
      clearSuggestions(suggestion);
    });
  });

  /**
   * Adding click event on submit button
   */
  submitBTN.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();

    // TODO make a great validation with css error maybe
    if (!!choosed_videos.length && !!current_username_id && !!new_username_id) {
      // Show loader on the videos container / disable submit button
      addRemoveLoader(videos_container);
      const saveText = submitBTN.textContent;
      submitBTN.textContent = "Changement en cours...";
      submitBTN.setAttribute("disabled", true);
      const url = `${update_videos_url}${current_username_id}/`;
      const token =
        document.querySelector("input[name=csrfmiddlewaretoken]").value ||
        Cookies.get("csrftoken");
      const data = {
        videos: choosed_videos,
        owner: new_username_id,
      };
      makeRequest(url, "POST", JSON.stringify(data), (csrf = token))
        .then((response) => {
          // Remove loader on videos container / undisable submit button
          addRemoveLoader(videos_container, true);
          submitBTN.textContent = saveText;
          submitBTN.removeAttribute("disabled");
          if (response.success) {
            document
              .querySelector("main")
              .appendChild(new AlertMessage(gettext(response.detail)));
          } else {
            document
              .querySelector("main")
              .appendChild(
                new AlertMessage(
                  gettext(response.detail),
                  (alert_class = "danger"),
                ),
              );
          }
          reset(); // reset fields
        })
        .catch((error) => {
          document
            .querySelector("main")
            .appendChild(
              new AlertMessage(
                gettext("An error occurred during the change of owner"),
                (alert_class = "danger"),
              ),
            );
          console.error(error);
        });
    } else {
      document
        .querySelector("main")
        .appendChild(
          new AlertMessage(
            gettext("Please complete all fields correctly"),
            (alert_class = "danger"),
          ),
        );
    }
  });

  /**
   * Reset all fields
   */
  const reset = (notOwnerInputs = false) => {
    if (!notOwnerInputs) {
      new_owner_input.value = "";
      old_owner_input.value = "";
    }
    selectAllVideos.checked = false;
    DATA = { count: 0, next: null, previous: null, results: [] };
    videos_container.innerHTML = "";
    list_videos__search.value = "";
    list_videos__search.nextElementSibling.innerHTML = "";
    choosed_videos = [];
    refreshPageInfos(null);
    refreshPagination();
    current_username_id = null;
    can_filter = false;
  };
})();
