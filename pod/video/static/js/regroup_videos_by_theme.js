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

  const limit = 8;
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
        return response;
      });
    });
  };

  const createVideoElement = (video) => {
    let has_password = () => {
      let span = ``;
      let title = gettext("This content is password protected.");
      if (video.has_password) {
        span = `<span title="${title}"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-lock align-bottom"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg></span>`;
      }
      return span;
    };
    let has_chapter = () => {
      let span = ``;
      let title = gettext("This content is chaptered.");
      if (video.has_chapter) {
        span = `<span title="${title}"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-list align-bottom"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3" y2="6"></line><line x1="3" y1="12" x2="3" y2="12"></line><line x1="3" y1="18" x2="3" y2="18"></line></svg></span>`;
      }
      return span;
    };
    let is_draft = () => {
      let span = ``;
      let title = gettext("This content is in draft.");
      if (video.is_draft) {
        span = `<span title="${title}">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-x-circle align-bottom"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg></span>`;
      }
      return span;
    };
    let is_video = () => {
      let span = ``;
      let title = gettext("Video content.");
      if (video.is_video) {
        span = `<span title="${title}">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-film align-bottom"><rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"></rect><line x1="7" y1="2" x2="7" y2="22"></line><line x1="17" y1="2" x2="17" y2="22"></line><line x1="2" y1="12" x2="22" y2="12"></line><line x1="2" y1="7" x2="7" y2="7"></line><line x1="2" y1="17" x2="7" y2="17"></line><line x1="17" y1="17" x2="22" y2="17"></line><line x1="17" y1="7" x2="22" y2="7"></line></svg></span>`;
      } else {
        title = gettext("Audio content.");
        span = `<span title="${title}"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-radio"><circle cx="12" cy="12" r="2"></circle><path d="M16.24 7.76a6 6 0 0 1 0 8.49m-8.48-.01a6 6 0 0 1 0-8.49m11.31-2.82a10 10 0 0 1 0 14.14m-14.14 0a10 10 0 0 1 0-14.14"></path></svg></i></span>`;
      }
      return span;
    };
    let edit_text = gettext("Edit the video");
    let completion_text = gettext("Complete the video");
    let chapter_text = gettext("Chapter the video");
    let delete_text = gettext("Delete the video");
    let infinite_item = document.createElement("div");
    infinite_item.setAttribute(
      "class",
      "infinite-item col-12 col-md-6 col-lg-3 mb-2 card-group"
    );
    infinite_item.setAttribute("style", "min-width: 12rem; min-height: 11rem;");
    infinite_item.setAttribute("data-slug", video.slug);
    let card = document.createElement("div");
    card.setAttribute(
      "class",
      "card mb-4 box-shadow border-secondary video-card"
    );
    card.innerHTML = `
      <div class="card-header">
        <div class="d-flex justify-content-between align-items-center">
          <small class="text-muted time">${video.duration}</small>
          <span class="text-muted small">
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
    }" title="${video.title.charAt(0).toUpperCase()}${video.title.slice(1)}">
          ${video.thumbnail}
        </a>
      </div>
      <div class="card-body px-3 py-2">
        <footer class="card-footer card-footer-pod p-0 m-0">
          <a href="${EDIT_URL}${
      video.slug
    }" title="${edit_text}" class="btn btn-light btn-sm p-0 pb-1 m-0 ml-1">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-edit align-bottom"><path d="M20 14.66V20a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h5.34"></path><polygon points="18 2 22 6 12 16 8 16 8 12 18 2"></polygon></svg>
          </a>
          <a href="${COMPLETION_URL}${
      video.slug
    }" title="${completion_text}" class="btn btn-light btn-sm p-0 pb-1 m-0 ml-1">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-file-text align-bottom"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
          </a>
          <a href="${CHAPTER_URL}${
      video.slug
    }" title="${chapter_text}" class="btn btn-light btn-sm p-0 pb-1 m-0 ml-1">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-list align-bottom"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3" y2="6"></line><line x1="3" y1="12" x2="3" y2="12"></line><line x1="3" y1="18" x2="3" y2="18"></line></svg>
          </a>
          <a href="${DELETE_URL}${
      video.slug
    }" title="${delete_text}" class="btn btn-light btn-sm p-0 pb-1 m-0 ml-1">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-trash-2 align-bottom"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
          </a>
        </footer>
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
      "btn btn-sm btn-outline-secondary text-truncate child-theme"
    );
    li.setAttribute("title", theme.title);
    const link = document.createElement("A");
    link.setAttribute("href", `${URLPathName}${theme.slug}/`);
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
  if (!has_more_themes && next_btn && !next_btn.classList.contains("disable"))
    next_btn.classList.add("disable");
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
    if (this.classList.contains("disable")) return;
    const themes_contents = scroll_wrapper.querySelectorAll(
      ".list-children-theme"
    );
    if (this.isEqualNode(next_btn) && curr_page < Number.parseInt(max_pages)) {
      current_position -= 100;
      // swipe content on the right
      themes_contents.forEach(
        (theme_content) =>
          (theme_content.style.transform = `translateX(${current_position}%)`)
      );
      previous_btn.classList.remove("disable");
      loadNextListThemeElement();
    } else if (this.isEqualNode(previous_btn) && current_position < 0) {
      current_position += 100;
      next_btn.classList.remove("disable");
      if (current_position == 0) previous_btn.classList.add("disable");
      // swipe content on the left
      themes_contents.forEach(
        (theme_content) =>
          (theme_content.style.transform = `translateX(${current_position}%)`)
      );
    }
    curr_page = Math.abs(current_position) / 100 + 1;
    if (
      curr_page === Number.parseInt(max_pages) &&
      !next_btn.classList.contains("disable")
    )
      next_btn.classList.add("disable");

    if (current_position === 0 && !previous_btn.classList.contains("disable"))
      previous_btn.classList.add("disable");
    current_page_info.innerText = `${curr_page}${PAGE_INFO_SEPARATOR}${max_pages}`;
    current_page_info.setAttribute(
      "title",
      `${curr_page}${PAGE_INFO_SEPARATOR}${max_pages}`
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
    video_loader_btn.textContent = gettext("Loading videos..");
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
    ".video-section #load-more-videos"
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
