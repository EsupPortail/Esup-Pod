import { Helper } from "/static/js/utils.js";

function run(has_more_themes, Helper) {
  const URLPathName = window.location.pathname;
  const scroll_wrapper = document.querySelector(".scroll_wrapper");
  const videos_container = document.querySelector("#videos_list");
  const EDIT_URL = `${window.location.origin}/video_edit/`;
  const COMPLETION_URL = `${window.location.origin}/video_completion/`;
  const CHAPTER_URL = `${window.location.origin}/video_chapter/`;
  const DELETE_URL = `${window.location.origin}/video_delete/`;
  const VIDEO_URL = `${window.location.origin}/video/`;
  const previous_btn = document.querySelector(".paginator .previous_content");
  const current_page_info = document.querySelector(".paginator .pages_infos");
  const next_btn = document.querySelector(".paginator .next_content");
  const PAGE_INFO_SEPARATOR = "/";

  const limit = 12;
  let current_video_offset = limit;
  let current_theme_offset = limit;
  let current_position = 0;
  let current_page = `1${PAGE_INFO_SEPARATOR}1`;

  /**
   * Make request to url
   * @param {String} url request url
   * @param {String} method request method
   * @param {FormData} body post data
   * @returns {Promise} json response
   */
  const makeRequest = (url, method = "GET", body = new FormData()) => {
    //console.log(`Making request '${url}'`);
    const data = {
      method,
      headers: {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": Cookies.get("csrftoken"),
        Accept: "application/json",
      },
    };
    if (method.toLowerCase() === "post") data["body"] = body;
    return fetch(url, data).then((data) => {
      return data.json().then((response) => {
        //console.log(response);
        return response;
      });
    });
  };

  const createVideoElement = (video) => {
    let has_password = () => {
      let span = ``;
      let title = gettext("This content is password protected.");
      if (video.has_password) {
        span = `<span title="${title}"><i class="bi bi-lock" aria-hidden="true"></i></span>`;
      }
      return span;
    };
    let has_chapter = () => {
      let span = ``;
      let title = gettext("This content is chaptered.");
      if (video.has_chapter) {
        span = `<span title="${title}"><i class="bi bi-card-list" aria-hidden="true"></i></span>`;
      }
      return span;
    };
    let is_draft = () => {
      let span = ``;
      let title = gettext("This content is in draft.");
      if (video.is_draft) {
        span = `<span title="${title}">
        <i class="bi bi-incognito"></i></span>`;
      }
      return span;
    };
    let is_video = () => {
      let span = ``;
      let title = gettext("Video content.");
      if (video.is_video) {
        span = `<span title="${title}">
        <i class="bi bi-film"></i></span>`;
      } else {
        title = gettext("Audio content.");
        span = `<span title="${title}"><i class="bi bi-soundwave" aria-hidden="true"></i></span>`;
      }
      return span;
    };
    let edit_text = gettext("Edit the video");
    let completion_text = gettext("Complete the video");
    let chapter_text = gettext("Chapter the video");
    let delete_text = gettext("Delete the video");
    let infinite_item = document.createElement("div");
    infinite_item.setAttribute("class", "infinite-item card-group");
    //infinite_item.setAttribute("style", "min-width: 12rem; min-height: 11rem;");
    infinite_item.setAttribute("data-slug", video.slug);
    let card = document.createElement("div");
    card.setAttribute("class", "card box-shadow pod-card--video video-card");
    let footer = ``;
    if (video.is_editable) {
      footer = `<footer class="card-footer card-footer-pod p-0 m-0">
        <a href="${EDIT_URL}${video.slug}" title="${edit_text}" class="btn pod-btn-social p-1 m-0 ms-1">
          <i class="bi bi-pencil-square" aria-hidden="true"></i></a>
                <a href="${COMPLETION_URL}${video.slug}" title="${completion_text}" class="btn pod-btn-social p-1 m-0 ms-1">
          <i class="bi bi-file-text" aria-hidden="true"></i></a>
                <a href="${CHAPTER_URL}${video.slug}" title="${chapter_text}" class="btn pod-btn-social p-1 m-0 ms-1">
          <i class="bi bi-card-list" aria-hidden="true"></i></a>
                <a href="${DELETE_URL}${video.slug}" title="${delete_text}" class="btn pod-btn-social p-1 m-0 ms-1">
          <i class="bi bi-trash" aria-hidden="true"></i></a>
        </footer>`;
    }
    card.innerHTML = `
      <div class="card-header">
        <div class="d-flex justify-content-between align-items-center">
          <small class="text-muted time">${video.duration}</small>
          <span class="text-muted small d-flex">
            ${has_password()}
            ${is_draft()}
            ${has_chapter()}
            ${is_video()}
          </span>
        </div>
      </div>
      <div class="card-thumbnail">
        <a class="link-center-pod" href="${VIDEO_URL}${
          video.slug
        }" title="${video.title.charAt(0).toUpperCase()}${video.title.slice(
          1,
        )}">
          ${video.thumbnail}
        </a>
      </div>
      <div class="card-body px-3 py-2">
        ${footer}
        <span class="small video-title">
          <a href="${VIDEO_URL}${video.slug}">${video.title
            .charAt(0)
            .toUpperCase()}${video.title.slice(1)}</a>
        </span>
      </div>
    `;
    infinite_item.appendChild(card);
    return infinite_item;
  };

  /**
   * Create an HTMLLiElement wich content a link element
   * @param {String} title
   * @param {String} slug
   */
  const createThemeElement = (theme) => {
    const li = document.createElement("LI");
    li.setAttribute(
      "class",
      "btn btn-sm btn-outline-secondary text-truncate child-theme",
    );
    li.setAttribute("title", theme.title);
    const link = document.createElement("A");
    let hrefUrl =
      document.querySelector(".themes-videos").dataset.channelurl + theme.slug;
    link.setAttribute("href", hrefUrl);
    link.setAttribute("class", "text-truncate");
    link.innerText = theme.title;

    li.appendChild(link);
    return li;
  };

  /**
   * Load more themes
   */
  const loadNextListThemeElement = () => {
    if (has_more_themes) {
      const url =
        window.location.href +
        `?limit=${limit}&offset=${current_theme_offset}&target=themes`;
      makeRequest(url).then((response) => {
        current_page = response.pages_info;
        has_more_themes = response.has_more_themes;
        current_theme_offset += limit;
        const ul = document.createElement("UL");
        ul.setAttribute("class", "list-children-theme");
        response.theme_children.forEach((child_theme) => {
          ul.appendChild(createThemeElement(child_theme));
        });
        scroll_wrapper.appendChild(ul);
      });
    }
  };
  // Disable next btn if no more themes to load
  if (!has_more_themes && next_btn && !next_btn.classList.contains("disabled"))
    next_btn.classList.add("disabled");
  // Load next list of theme
  loadNextListThemeElement();

  /**
   * listener to next/previous buttons
   * @param {ClickEvent} e
   */
  const nextPreviousHandler = function (e) {
    e.preventDefault();
    e.stopPropagation();
    let curr_page = Math.abs(current_position) / 100 + 1;
    const [_, max_pages] = current_page.split(PAGE_INFO_SEPARATOR);
    if (this.classList.contains("disabled")) return;
    const themes_contents = scroll_wrapper.querySelectorAll(
      ".list-children-theme",
    );
    if (this.isEqualNode(next_btn) && curr_page < Number.parseInt(max_pages)) {
      current_position -= 100;
      // swipe content on the right
      themes_contents.forEach(
        (theme_content) =>
          (theme_content.style.transform = `translateX(${current_position}%)`),
      );
      previous_btn.classList.remove("disabled");
      loadNextListThemeElement();
    } else if (this.isEqualNode(previous_btn) && current_position < 0) {
      current_position += 100;
      next_btn.classList.remove("disabled");
      if (current_position == 0) previous_btn.classList.add("disabled");
      // swipe content on the left
      themes_contents.forEach(
        (theme_content) =>
          (theme_content.style.transform = `translateX(${current_position}%)`),
      );
    }
    curr_page = Math.abs(current_position) / 100 + 1;
    if (
      curr_page === Number.parseInt(max_pages) &&
      !next_btn.classList.contains("disabled")
    )
      next_btn.classList.add("disabled");

    if (current_position === 0 && !previous_btn.classList.contains("disabled"))
      previous_btn.classList.add("disabled");
    current_page_info.innerText = `${curr_page}${PAGE_INFO_SEPARATOR}${max_pages}`;
    current_page_info.setAttribute(
      "title",
      `${curr_page}${PAGE_INFO_SEPARATOR}${max_pages}`,
    );
  };

  /**
   * Manage next/ previous  click Event
   */
  [previous_btn, next_btn].forEach((btn) => {
    if (!!btn) btn.addEventListener("click", nextPreviousHandler);
  });

  /**
   * loading more videos handler
   * @param {ClickEvent} e
   */
  const loadMoreVideos = (e) => {
    e.preventDefault();
    e.stopPropagation();
    const url =
      window.location.href +
      `?limit=${limit}&offset=${current_video_offset}&target=videos`;
    // Chargement vidéos..
    const save_text = video_loader_btn.textContent;
    video_loader_btn.textContent = gettext("Loading videos…");
    video_loader_btn.setAttribute("disabled", "disabled");
    makeRequest(url).then((response) => {
      current_video_offset += limit;
      video_loader_btn.textContent = save_text;
      video_loader_btn.removeAttribute("disabled");
      if (!response.has_more_videos) video_loader_btn.remove();
      response.videos.forEach((v) => {
        videos_container.appendChild(createVideoElement(v));
      });
    });
  };
  const video_loader_btn = document.querySelector(
    ".video-section #load-more-videos",
  );
  if (!!video_loader_btn) {
    video_loader_btn.addEventListener("click", loadMoreVideos);
    // Overriding click event to loading more videos
    let loadOnce = true;
    let alreadyClicked = false;
    window.onscroll = function (e) {
      const isVisible = Helper.isElementInView(video_loader_btn);
      if (isVisible && loadOnce) {
        video_loader_btn.click();
        alreadyClicked = true;
      }
      if (alreadyClicked) loadOnce = !isVisible;
    };
  }
}
run(has_more_themes, Helper);
