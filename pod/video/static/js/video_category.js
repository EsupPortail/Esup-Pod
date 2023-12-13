(function (CATEGORIES_DATA) {
  const SERVER_DATA = CATEGORIES_DATA.filter((c) => !Number.isInteger(c));
  // Category to delete
  const CAT_TO_DELETE = {
    html: undefined,
    id: undefined,
    slug: undefined,
  };
  const VIDEOS_LIST_CHUNK = {
    videos: {
      chunk: [], // all videos chunked
      selected: [], // current selected videos
      unselected: [], // current unselected videos
    }, // all videos
    page_index: 0, // current index
    size: 12, // videos per page
  };
  const modal_video_list = document.querySelector(
    ".category_modal_videos_list",
  );
  const msg_saved = gettext("Category changes saved successfully");
  const msg_error_duplicate = gettext(
    "You cannot add two categories with the same title.",
  );
  const msg_deleted = gettext("Category deleted successfully");
  const msg_error = gettext(
    "An error occured, please refresh the page and try again.",
  );
  const msg_title_empty = gettext("Category title field is required.");
  const msg_save_cat = gettext("Save category");
  let videos_list = document.querySelector(
    "#videos_list.infinite-container:not(.filtered)",
  );
  let saveCatBtn = document.querySelector("#manageCategoryModal #saveCategory"); // btn in dialog
  let modal_title = document.querySelector("#manageCategoryModal #modal_title");
  let cat_input = document.querySelector("#manageCategoryModal #catTitle");
  let CURR_CATEGORY = {}; // current editing category (js object)
  let DOMCurrentEditCat = null; // current editing category (html DOM)
  // show loader
  let loader = document.querySelector(".lds-ring");

  const SAVED_DATA = {}; // To prevent too many requests to the server
  const CURR_FILTER = { slug: null, id: null }; // the category currently filtering
  const HEADERS = {
    "Content-Type": "application/json",
    "X-Requested-With": "XMLHttpRequest",
    "X-CSRFToken": Cookies.get("csrftoken"),
    Accept: "application/json",
  };

  // show paginate video
  const show_paginate_videos = (paginator = true) => {
    if (paginator) modal_video_list.classList.add("show");
    const html_paginator = modal_video_list.querySelector(".paginator");
    modal_video_list.innerHTML = "";
    modal_video_list.appendChild(html_paginator);
    if (VIDEOS_LIST_CHUNK.videos.chunk.length > 0) {
      let videos_to_display =
        VIDEOS_LIST_CHUNK.videos.chunk[VIDEOS_LIST_CHUNK.page_index];
      videos_to_display.forEach((v) => appendVideoCard(toggleSelectedClass(v)));
    } else {
      const cat_modal_alert = document.createElement("div");
      cat_modal_alert.setAttribute("class", "alert alert-warning");
      cat_modal_alert.innerHTML = gettext(
        "You have no content without a category.",
      );
      const cat_modal_body = document.querySelector(
        "#manageCategoryModal .modal-body",
      );
      cat_modal_body.appendChild(cat_modal_alert);
    }
  };
  // Chunk array
  const chunk = (arr, size) =>
    Array.from({ length: Math.ceil(arr.length / size) }, (v, i) =>
      arr.slice(i * size, i * size + size),
    );
  const paginate = (cat_videos) => {
    VIDEOS_LIST_CHUNK.page_index = 0;
    prev.classList.add("disabled");
    const video_elements = Array.from(
      modal_video_list.querySelectorAll(
        ".category_modal_videos_list .infinite-item",
      ),
    );
    VIDEOS_LIST_CHUNK.videos.selected = cat_videos.map((v) =>
      getModalVideoCard(v),
    );

    // Saving unselected videos
    if (video_elements.length && !VIDEOS_LIST_CHUNK.videos.unselected.length) {
      VIDEOS_LIST_CHUNK.videos.unselected = video_elements.filter(
        (html_v) => !html_v.classList.contains("selected"),
      );
    }
    VIDEOS_LIST_CHUNK.videos.chunk = chunk(
      [
        ...VIDEOS_LIST_CHUNK.videos.unselected,
        ...VIDEOS_LIST_CHUNK.videos.selected,
      ],
      VIDEOS_LIST_CHUNK.size,
    );
    pages_info.innerText = `${VIDEOS_LIST_CHUNK.page_index + 1}/${
      VIDEOS_LIST_CHUNK.videos.chunk.length
    }`;
    pages_info.setAttribute(
      "title",
      `${VIDEOS_LIST_CHUNK.page_index + 1}/${
        VIDEOS_LIST_CHUNK.videos.chunk.length
      }`,
    );
    if (VIDEOS_LIST_CHUNK.videos.chunk.length > 1) {
      modal_video_list.classList.add("show");
      modal_video_list
        .querySelector(".next_content")
        .classList.remove("disabled");
      show_paginate_videos();
    } else {
      show_paginate_videos(false);
      modal_video_list.classList.remove("show");
    }
  };

  // Add event to paginate
  let pages_info = document.querySelector(".paginator .pages_infos");
  let next = document.querySelector(".paginator .next_content");
  let prev = document.querySelector(".paginator .previous_content");
  prev.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    VIDEOS_LIST_CHUNK.page_index -= VIDEOS_LIST_CHUNK.page_index > 0 ? 1 : 0;
    let nbr_pages = VIDEOS_LIST_CHUNK.videos.chunk.length - 1;
    if (VIDEOS_LIST_CHUNK.page_index === 0) prev.classList.add("disabled");
    next.classList.remove("disabled");
    pages_info.innerText = `${VIDEOS_LIST_CHUNK.page_index + 1}/${
      nbr_pages + 1
    }`;
    pages_info.setAttribute(
      "title",
      `${VIDEOS_LIST_CHUNK.page_index + 1}/${nbr_pages + 1}`,
    );
    show_paginate_videos();
  });
  next.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    let nbr_pages = VIDEOS_LIST_CHUNK.videos.chunk.length - 1;
    VIDEOS_LIST_CHUNK.page_index +=
      VIDEOS_LIST_CHUNK.page_index < nbr_pages ? 1 : 0;
    if (VIDEOS_LIST_CHUNK.page_index === nbr_pages)
      next.classList.add("disabled");

    prev.classList.remove("disabled");
    pages_info.innerText = `${VIDEOS_LIST_CHUNK.page_index + 1}/${
      nbr_pages + 1
    }`;
    pages_info.setAttribute(
      "title",
      `${VIDEOS_LIST_CHUNK.page_index + 1}/${nbr_pages + 1}`,
    );
    show_paginate_videos();
  });

  // Search categery
  let searchCatInput = document.getElementById("searchcategories");
  let searchCatHandler = (s) => {
    let cats = document.querySelectorAll(
      ".categories_list .cat_title:not(.hidden)",
    );
    if (s.length >= 3) {
      cats.forEach((cat) => {
        if (!cat.innerHTML.trim().toLowerCase().includes(s))
          cat.parentNode.classList.add("hidden");
        else cat.parentNode.classList.remove("hidden");
      });
    } else {
      cats = document.querySelectorAll(".categories_list .hidden");
      cats.forEach((cat) => {
        cat.classList.remove("hidden");
      });
    }
  };
  searchCatInput.addEventListener("input", (e) => {
    searchCatHandler(searchCatInput.value.trim());
  });

  // Update text 'Number video found' on filtering
  let manageNumberVideoFoundText = (v_len) => {
    let text = v_len > 1 ? gettext("videos found") : gettext("video found");
    let h2 = document.querySelector(".pod-mainContent h2");
    h2.textContent = `${v_len} ${text}`;
    if (!v_len) {
      text = gettext("Sorry, no video found");
      getVideosFilteredContainer().innerHTML = `<p class="alert alert-warning" role="alert">${text}</p>`;
    } else {
      // delete warning text videos found
      let warning = document.querySelector(
        "#videos_list.filtered .alert-warning",
      );
      if (warning) warning.parentNode.removeChild(warning);
    }
  };

  // Add/Remove active class on category, html_el = <li></li>
  let manageCssActiveClass = (html_el) => {
    html_el.parentNode
      .querySelectorAll(".categories_list_item")
      .forEach((c_p) => {
        c_p.classList.remove("active");
      });
    let curr_slug = html_el.querySelector(".cat_title").dataset.slug;
    let curr_id = html_el.querySelector(".remove_category").dataset.del;
    html_el.classList.toggle("active");
    getVideosFilteredContainer().innerHTML = "";
    if (CURR_FILTER.slug === curr_slug && CURR_FILTER.id == curr_id) {
      html_el.classList.remove("active"); // unfilter
      CURR_FILTER.slug = null;
      CURR_FILTER.id = null;
      getVideosFilteredContainer().classList.add("hidden");
      if (videos_list) {
        videos_list.setAttribute(
          "class",
          "pod-infinite-container infinite-container",
        );
      }
    } else {
      // filter
      html_el.classList.add("active");
      let { id, slug } = findCategory(curr_slug, curr_id);
      CURR_FILTER.id = id;
      CURR_FILTER.slug = slug;

      getVideosFilteredContainer().classList.remove("hidden");

      if (videos_list) {
        videos_list.setAttribute(
          "class",
          "pod-infinite-container infinite-container hidden",
        );
      }
    }
  };

  // Create filtered videos container (HtmlELement)
  let getVideosFilteredContainer = () => {
    let videos_list_filtered = document.querySelector(
      ".pod-mainContent .filtered.infinite-container",
    );
    if (videos_list_filtered) {
      return videos_list_filtered;
    }
    videos_list_filtered = document.createElement("div");
    videos_list_filtered.setAttribute(
      "class",
      "filtered infinite-container pod-infinite-container",
    );
    videos_list_filtered.setAttribute("id", "videos_list");
    document
      .querySelector(".pod-mainContent .pod-first-content")
      .appendChild(videos_list_filtered);
    return videos_list_filtered;
  };
  // Update videos Filtered in filtered container after editing category
  let updateFilteredVideosContainer = (category_data) => {
    if (
      CURR_FILTER.slug &&
      CURR_FILTER.id &&
      CURR_CATEGORY.slug === CURR_FILTER.slug &&
      CURR_CATEGORY.id === CURR_FILTER.id
    ) {
      let actual_videos = VIDEOS_LIST_CHUNK.videos.selected.map(
        (v_html) => v_html.dataset.slug,
      );
      let old_videos = getSavedData(CURR_FILTER.id).videos.map((v) => v.slug);
      let rm = old_videos.filter((v) => !actual_videos.includes(v));
      let added = actual_videos.filter((v) => !old_videos.includes(v));
      let container_filtered = getVideosFilteredContainer();

      let maxLen = rm.length > added.length ? rm.length : added.length;
      for (let i = 0; i < maxLen; i++) {
        // remove video that was deselected when editing category
        if (rm[i]) {
          container_filtered.removeChild(
            container_filtered.querySelector(
              `.infinite-item[data-slug="${rm[i]}"`,
            ),
          );
        }

        // Add video that was selected when editing category
        if (added[i]) {
          container_filtered.appendChild(
            getVideoElement(
              category_data.videos.find((v) => v.slug === added[i]),
            ),
          );
        }
      }
      manageNumberVideoFoundText(actual_videos.length);
    }
  };

  // Add click event to manage filter video on click category
  let manageFilterVideos = (c) => {
    c.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      let cat_filter_slug = c.dataset.slug.trim();
      let cat_filter_id = c.parentNode
        .querySelector(".category_actions .remove_category")
        .dataset.del.trim();
      manageCssActiveClass(c.parentNode); // manage active css class
      refreshVideosSearch();
    });
  };

  // remove all current selected videos in dialog
  let refreshDialog = () => {
    let videos = document.querySelectorAll(
      ".category_modal_videos_list .selected",
    );
    videos.forEach((v) => {
      v.parentNode.removeChild(v);
    });
  };

  // Save/update category data locally
  let saveCategoryData = (data) => {
    SAVED_DATA[`${data.id}`] = data;
  };

  // Delete category data locally
  let deleteFromSavedData = (c_slug) => {
    if (Object.keys(SAVED_DATA).includes(c_slug)) delete SAVED_DATA[id];
  };

  // Search cat by slug
  let findCategory = (slug, id = 0) => {
    let cat = SERVER_DATA.find((c) => c.slug === slug && c.id == id);
    if (!cat) cat = getSavedData((id = id));
    return cat;
  };

  // Get saved category data
  let getSavedData = (id) => {
    let cat = {};
    if (Object.keys(SAVED_DATA).includes(id.toString(10)))
      cat = SAVED_DATA[id.toString(10)];
    return cat;
  };

  // Add event toggle selected class on el
  let toggleSelectedClass = (el) => {
    if (el.dataset.hasevent != "true") {
      el.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        el.classList.toggle("selected");
        let selected = el.classList.contains("selected");
        if (selected) {
          VIDEOS_LIST_CHUNK.videos.unselected =
            VIDEOS_LIST_CHUNK.videos.unselected.filter(
              (v) => !v.classList.contains("selected"),
            );
          VIDEOS_LIST_CHUNK.videos.selected = [
            ...VIDEOS_LIST_CHUNK.videos.selected,
            el,
          ];
        } else {
          VIDEOS_LIST_CHUNK.videos.selected =
            VIDEOS_LIST_CHUNK.videos.selected.filter((v) =>
              v.classList.contains("selected"),
            );
          VIDEOS_LIST_CHUNK.videos.unselected = [
            ...VIDEOS_LIST_CHUNK.videos.unselected,
            el,
          ];
        }
      });
      el.setAttribute("data-hasevent", true);
    }
    return el;
  };

  // Make requets => get category data
  let fetchCategoryData = async (cat_slug) => {
    try {
      let resp = await fetch(`${BASE_URL}${cat_slug}/`, { headers: HEADERS });
      return await resp.json();
    } catch (e) {
      loader.classList.remove("show");
      showAlertMessage(msg_error, false, (delay = 30000));
    }
  };

  // Make post request. for edit or add category, postData(object)
  let postCategoryData = async (url, postData) => {
    try {
      let resp = await fetch(url, {
        method: "POST",
        body: JSON.stringify(postData),
        headers: HEADERS,
      });
      return await resp.json();
    } catch (e) {
      loader.classList.remove("show");
      showAlertMessage(msg_error_duplicate, false, (delay = 30000));
    }
  };

  let get_type_icon = (is_video = true) => {
    let videoContent_Text = gettext("Video content.");
    let audioContent_Text = gettext("Audio content.");
    if (is_video) {
      return '<span title="' + videoContent_Text + '">';
    }
    return '<span title="' + audioContent_Text + '">';
  };

  // Create category html element <li></li>
  let getCategoryLi = (title, slug, id) => {
    let btnEdit = document.createElement("button");
    btnEdit.setAttribute("title", gettext("Edit the category"));
    btnEdit.setAttribute("data-bs-toggle", "modal");
    btnEdit.setAttribute("data-bs-target", "#manageCategoryModal");
    btnEdit.setAttribute("data-slug", slug);
    btnEdit.setAttribute("data-title", title);
    btnEdit.setAttribute("class", "btn btn-link edit_category");
    btnEdit.innerHTML = `<i class="bi bi-pencil-square"></i>`;
    editHandler(btnEdit); // append edit click event

    let btnDelete = document.createElement("button");
    btnDelete.setAttribute("title", gettext("Delete the category"));
    btnDelete.setAttribute("data-bs-toggle", "modal");
    btnDelete.setAttribute("data-bs-target", "#deleteCategoryModal");
    btnDelete.setAttribute("data-del", id);
    btnDelete.setAttribute("data-slug", slug);
    btnDelete.setAttribute("data-title", title);
    btnDelete.setAttribute("class", "btn btn-link remove_category");
    btnDelete.innerHTML = `<i class="bi bi-trash"></i>`;
    deleteHandler(btnDelete); // append delete click event

    let li = document.createElement("li");
    li.setAttribute("class", "categories_list_item");
    li.innerHTML = `
      <div class="category_actions"></div>`;

    let catTitleHtml = document.createElement("button");
    catTitleHtml.setAttribute("class", "btn btn-link cat_title");
    catTitleHtml.setAttribute("data-slug", slug);
    catTitleHtml.innerText = title;
    manageFilterVideos(catTitleHtml); // append filter click event
    li.prepend(catTitleHtml);
    li.querySelector(".category_actions").appendChild(btnEdit);
    li.querySelector(".category_actions").appendChild(btnDelete);
    return li;
  };

  // Create video html element card for Category Dialog
  let createHtmlVideoCard = (v) => {
    return `
    <div class="checked_overlay">
      <span class="card_selected" id="card_selected">
        <svg aria-hidden="true" focusable="false" data-prefix="fas" data-icon="check-circle" class="svg-inline--fa fa-check-circle fa-w-16" role="img" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><path fill="currentColor" d="M504 256c0 136.967-111.033 248-248 248S8 392.967 8 256 119.033 8 256 8s248 111.033 248 248zM227.314 387.314l184-184c6.248-6.248 6.248-16.379 0-22.627l-22.627-22.627c-6.248-6.249-16.379-6.249-22.628 0L216 308.118l-70.059-70.059c-6.248-6.248-16.379-6.248-22.628 0l-22.627 22.627c-6.248 6.248-6.248 16.379 0 22.627l104 104c6.249 6.249 16.379 6.249 22.628.001z"></path></svg>
      </span>
    </div><div class="card modal_category_card mb-4 box-shadow border-secondary video-card">
      <div class="card-header">
        <div class="d-flex justify-content-between align-items-center">
          <small class="text-muted time">${v.duration}</small>
          <span class="text-muted small">${get_type_icon(v.is_video)}</span>
        </div>
      </div><div class="card-body">
        <a class="link-center-pod" href="#" title="${v.title}">
          ${v.thumbnail}
        </a>
      </div>
      <div class="card-footer">
        <span class="video_title">${v.title}</span>
      </div>
    </div>`;
  };

  // Create video video html element for my_videos (on filtering with category)
  // video = object
  let getVideoElement = (video) => {
    let span_info = `
      <span>
    `;
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
        <i class="bi bi-film" aria-hidden="true"></i></span>`;
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
    // infinite_item.setAttribute("style", "min-width: 12rem; min-height: 11rem;");
    infinite_item.setAttribute("data-slug", video.slug);
    let card = document.createElement("div");
    card.setAttribute(
      "class",
      "card box-shadow pod-card--video video-card", // "card mb-4 box-shadow border-secondary video-card"
    );
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
        <footer class="card-footer card-footer-pod p-0 m-0">
          <a href="${EDIT_URL}${
            video.slug
          }" title="${edit_text}" class="btn btn-link btn-lg pod-btn-social p-1 m-0 ms-1">
    <i class="bi bi-pencil-square" aria-hidden="true"></i></a>
          <a href="${COMPLETION_URL}${
            video.slug
          }" title="${completion_text}" class="btn btn-link btn-lg pod-btn-social p-1 m-0 ms-1">
    <i class="bi bi-file-text" aria-hidden="true"></i></a>
          <a href="${CHAPTER_URL}${
            video.slug
          }" title="${chapter_text}" class="btn btn-link btn-lg pod-btn-social p-1 m-0 ms-1">
    <i class="bi bi-card-list" aria-hidden="true"></i></a>
          <a href="${DELETE_URL}${
            video.slug
          }" title="${delete_text}" class="btn btn-link btn-lg pod-btn-social p-1 m-0 ms-1">
    <i class="bi bi-trash" aria-hidden="true"></i></a>
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

  // Create alert message
  let showAlertMessage = (message, type = true, delay = 4000) => {
    let success = gettext("Success!");
    let error = gettext("Error…");
    let title = type ? success : error;
    let class_suffix = type ? "success" : "danger";
    let icon =
      type === "success"
        ? `<i class="bi bi-check2-circle"></i>`
        : type === "error"
          ? `<i class="bi bi-exclamation-triangle"></i>`
          : `<i class="bi bi-info-circle"></i>`;
    let alert_message = document.createElement("div");
    alert_message.setAttribute(
      "class",
      `category_alert alert alert-${class_suffix}`,
    );
    alert_message.setAttribute("role", `alert`);
    alert_message.innerHTML = `<div class="alert_content"><span class="alert_icon">${icon}</span><span class="alert_title">${title}</span><span class="alert_text">${message}</span>`;
    document.body.appendChild(alert_message);
    window.setTimeout(() => alert_message.classList.add("show"), 1000);
    window.setTimeout(() => {
      alert_message.classList.add("hide");
      window.setTimeout(() => document.body.removeChild(alert_message), 1000);
    }, delay);
  };

  // Handler to edit category, c_e=current category to edit
  let editHandler = (c_e) => {
    c_e.addEventListener("click", (e) => {
      e.preventDefault();
      loader.classList.add("show");
      cat_edit_title = c_e.dataset.title.trim();
      cat_edit_slug = c_e.dataset.slug.trim();
      cat_edit_id = c_e.parentNode
        .querySelector(".remove_category")
        .dataset.del.trim();
      cat_input.value = cat_edit_title;
      modal_title.innerText = c_e.getAttribute("title").trim();
      window.setTimeout(function () {
        cat_input.focus();
      }, 500); // focus in input (category title)

      // add videos of the current category into the dialog
      saveCatBtn.setAttribute("data-action", "edit");
      saveCatBtn.innerText = msg_save_cat;
      let jsonData = getSavedData(cat_edit_id);
      CURR_CATEGORY = jsonData;
      DOMCurrentEditCat = c_e.parentNode.parentNode;
      if (Object.keys(jsonData).length) {
        paginate(jsonData.videos);
        loader.classList.remove("show");
      } else {
        jsonData = fetchCategoryData(cat_edit_slug);
        jsonData
          .then((data) => {
            paginate(data.videos);
            // save data
            saveCategoryData(data);
            CURR_CATEGORY = data;
            loader.classList.remove("show");
          })
          .catch((e) => {
            loader.classList.remove("show");
            showAlertMessage(msg_error, false, (delay = 30000));
          });
      }
    });
  };

  // get modal video card
  let getModalVideoCard = (v, selected = true) => {
    let videoCard = createHtmlVideoCard(v);
    let v_wrapper = document.createElement("Div");
    v_wrapper.setAttribute("data-slug", v.slug);
    let selectClass = selected ? "selected" : "";
    v_wrapper.setAttribute(
      "class",
      "infinite-item col-12 col-md-6 col-lg-3 mb-2 card-group " + selectClass,
    );
    v_wrapper.innerHTML = videoCard;
    return v_wrapper;
  };
  // Append video card in category modal
  let appendVideoCard = (v) => {
    let modalListVideo = document.querySelector(
      "#manageCategoryModal .category_modal_videos_list",
    );
    modalListVideo.insertBefore(v, modalListVideo.querySelector(".paginator"));
  };

  // Add onclick event to edit a category
  let cats_edit = document.querySelectorAll(
    ".categories_list_item .edit_category",
  );
  cats_edit.forEach((c_e) => {
    editHandler(c_e);
  });

  // Handler to delete category, c_d=current category to delete
  // Temporarily save the category to delete
  let deleteHandler = (c_d) => {
    c_d.addEventListener("click", (e) => {
      e.preventDefault();
      // Show confirm modal => manage by boostrap
      CAT_TO_DELETE.html = c_d.parentNode.parentNode;
      CAT_TO_DELETE.id = c_d.dataset.del;
      CAT_TO_DELETE.slug = c_d.dataset.slug;
      document.querySelector(
        "#deleteCategoryModal .modal-body .category_title",
      ).textContent = c_d.dataset.title;
    });
  };

  // Add onclick event to delete a category
  let cats_del = document.querySelectorAll(
    ".categories_list_item .remove_category",
  );
  cats_del.forEach((c_d) => {
    deleteHandler(c_d);
  });

  // Add onclick event to delete a category
  let del_cat = document.querySelector("#confirm_remove_category_btn");
  del_cat.addEventListener("click", (e) => {
    loader.classList.add("show");
    if (CAT_TO_DELETE.slug && CAT_TO_DELETE.id && CAT_TO_DELETE.html) {
      // Delete category
      let cat = findCategory(
        (slug = CAT_TO_DELETE.slug),
        (id = CAT_TO_DELETE.id),
      );
      if (Object.keys(cat).length) {
        fetch(`${BASE_URL}delete/${cat.id}/`, {
          method: "POST",
          headers: HEADERS,
        }).then((response) => {
          response.json().then((data) => {
            showAlertMessage(msg_deleted);
            deleteFromSavedData(cat.slug); // delete from local save

            // TODO : Ici il faudrait masquer la recherche si c'est la dernière cat supprimée, et l'afficher sinon.

            // Remove eventual alert message
            const cat_modal_alert = document.querySelector(
              "#manageCategoryModal .modal-body .alert-warning",
            );
            if (
              typeof cat_modal_alert != "undefined" &&
              cat_modal_alert != null
            ) {
              cat_modal_alert.remove();
            }
            data.videos.forEach((v) => {
              // append all the videos into chunk videos unselected
              VIDEOS_LIST_CHUNK.videos.unselected = [
                ...VIDEOS_LIST_CHUNK.videos.unselected,
                getModalVideoCard(v, false),
              ];
            });
            document
              .querySelector(".categories_list")
              .removeChild(CAT_TO_DELETE.html);
            let filtered_container = getVideosFilteredContainer();
            if (
              filtered_container &&
              CAT_TO_DELETE.id == CURR_FILTER.id &&
              CAT_TO_DELETE.slug === CURR_FILTER.slug
            ) {
              filtered_container.parentNode.removeChild(filtered_container);
              let my_videos_container = document.querySelector(
                ".infinite-container.hidden",
              );
              if (my_videos_container)
                my_videos_container.classList.remove("hidden");
              manageNumberVideoFoundText(CATEGORIES_DATA[0]);
              CURR_FILTER.slug = null;
              CURR_FILTER.id = null;
              document
                .querySelectorAll(".categories_list .categories_list_item")
                .forEach((c) => c.classList.remove("active"));
            }
            delete CAT_TO_DELETE.html;
            delete CAT_TO_DELETE.id;
            delete CAT_TO_DELETE.slug;
            loader.classList.remove("show");
            // close modal
            document
              .querySelector("#deleteCategoryModal .modal-footer .close_modal")
              .click();
          });
        });
      } else {
        //TODO display msg error cat
        loader.classList.remove("show");
      }
    } else {
      // display msg error like 'no category to delete'
      loader.classList.remove("show");
    }
  });

  // Add onclick event to save category (create or edit) data
  saveCatBtn.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();

    loader.classList.add("show");

    //let videos = Array.from(document.querySelectorAll(".category_modal_videos_list .selected")).map(v_el => v_el.dataset.slug.trim());
    const videos = VIDEOS_LIST_CHUNK.videos.selected.map(
      (html_v) => html_v.dataset.slug,
    );
    let postData = {
      title: cat_input.value.trim(),
      videos: videos,
    };
    if (cat_input.value.trim() === "") {
      showAlertMessage(msg_title_empty, false, (delay = 30000));
      loader.classList.remove("show");
      return;
    }

    if (Object.keys(CURR_CATEGORY).length > 0 && DOMCurrentEditCat) {
      // Editing mode
      // Update new data, server side
      postCategoryData(`${BASE_URL}edit/${CURR_CATEGORY.slug}/`, postData)
        .then((data) => {
          // Update new data, client side
          updateFilteredVideosContainer(data); // update filered videos in filtered container
          deleteFromSavedData(CURR_CATEGORY.slug);
          saveCategoryData(data);
          DOMCurrentEditCat.querySelector(".cat_title").textContent =
            data.title;
          DOMCurrentEditCat.querySelector(".cat_title").setAttribute(
            "title",
            data.title,
          );
          DOMCurrentEditCat.querySelectorAll("span").forEach((sp) => {
            sp.setAttribute("data-slug", data.slug);
            sp.setAttribute("data-title", data.title);
          });
          DOMCurrentEditCat = null;
          CURR_CATEGORY = {};
          // close modal
          document.querySelector("#manageCategoryModal #cancelDialog").click();
          refreshDialog();
          showAlertMessage(msg_saved);
          loader.classList.remove("show"); // hide loader
        })
        .catch((err) => {
          loader.classList.remove("show");
          showAlertMessage(msg_error, false, (delay = 30000));
        });
    } else {
      // Adding mode
      postCategoryData(`${BASE_URL}add/`, postData)
        .then((data) => {
          let li = getCategoryLi(
            data.category.title,
            data.category.slug,
            data.category.id,
          );
          document.querySelector(".categories_list").appendChild(li);
          let msg_create = gettext("Category created successfully");
          showAlertMessage(msg_create);
          saveCategoryData(data.category); // saving cat localy to prevent more request to the server
          loader.classList.remove("show"); // hide loader
        })
        .catch((err) => {
          //alert(err);
          showAlertMessage(msg_error_duplicate, false, (delay = 30000));
        });
      document.querySelector("#manageCategoryModal #cancelDialog").click();
      refreshDialog();
    }
  });

  // Add onclick event to add a new category
  let add_cat = document.querySelector("#add_category_btn");
  add_cat.addEventListener("click", (e) => {
    paginate([]);
    modal_title.innerText = gettext("Add new category");
    cat_input.value = "";
    // Change the Save button text to 'create category'
    saveCatBtn.textContent = gettext("Create category");
    saveCatBtn.setAttribute("data-action", "create");
    CURR_CATEGORY = {};
    window.setTimeout(function () {
      cat_input.focus();
    }, 500);
  });

  // Add click event on category in filter bar to filter videos in my_videos vue
  let cats = document.querySelectorAll(".categories_list_item .cat_title");
  cats.forEach((c) => {
    manageFilterVideos(c);
  });
})(JSON.parse(JSON.stringify(CATEGORIES_DATA)));
