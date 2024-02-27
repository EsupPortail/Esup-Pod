/**
 * Esup-Pod video category scripts.
 */
document.getElementById("add_category_btn").addEventListener("click", () => {
  get_category_modal(CATEGORIES_ADD_URL);
});

function manageCategoriesLinks(){
    Array.from(document.getElementsByClassName("edit_category_btn")).forEach((el) => {
      el.addEventListener("click", () => {
        let url_edit = getCategoriesUrl("edit", el.dataset.slug);
        get_category_modal(url_edit);
      });
    });

    Array.from(document.getElementsByClassName("delete_category_btn")).forEach((el) => {
      el.addEventListener("click", () => {
        let url_delete = getCategoriesUrl("delete", el.dataset.slug);
        get_category_modal(url_delete);
      });
    });
}

let searchCategoriesInput = document.getElementById("searchCategoriesInput");
if(searchCategoriesInput){
    searchCategoriesInput.addEventListener("input", () => {
        manageSearchCategories(searchCategoriesInput.value.trim());
    });
}

function toggleCategoryLink(el) {
    el.parentNode.classList.toggle("active");
    refreshVideosSearch();
}

function manageSearchCategories(search){
    let categories = document.querySelectorAll(
      ".categories_list .cat_title:not(.hidden)",
    );
    if (search.length >= 3) {
      categories.forEach((cat) => {
        if (!cat.innerHTML.trim().toLowerCase().includes(search))
          cat.parentNode.classList.add("hidden");
        else cat.parentNode.classList.remove("hidden");
      });
    } else {
      categories = document.querySelectorAll(".categories_list .hidden");
      categories.forEach((cat) => {
        cat.classList.remove("hidden");
      });
    }
}

function get_category_modal(url){
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
      // Parse data into html and create new modal
      let parser = new DOMParser();
      let html = parser.parseFromString(data, "text/html").body;
      categoryModal.innerHTML = html.innerHTML;
      new bootstrap.Modal(document.getElementById('category_modal')).toggle();
      manageModalConfirmBtn();
    })
    .catch(() => {
      showalert(gettext("An Error occurred while processing."), "alert-danger", "formalertdivbottomright");
    });
}

function post_category_modal(url){
    let formData = new FormData();
    let selected_videos_categories = getCategoriesSelectedVideosSlugs();
    formData.append("videos", JSON.stringify(selected_videos_categories));
    if(document.getElementById("catTitle")){
        formData.append("title", document.getElementById("catTitle").value);
    }

    fetch(url, {
    method: "POST",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": csrftoken,
    },
    body: formData,
    cache: "no-store",
  })
    .then((response) => response.text())
    .then((data) => {
      data = JSON.parse(data);
      bootstrap.Modal.getInstance(categoryModal).toggle();
      showalert(data["message"], "alert-success", "formalertdivbottomright");
      refreshCategoriesLinks();
    })
    .catch(() => {
      showalert(gettext("An Error occurred while processing."), "alert-danger", "formalertdivbottomright");
    });
}

function manageModalConfirmBtn(){
    let btn = document.getElementById("confirm_category_btn");
    if(btn !== undefined && btn.dataset.action !== undefined){
        btn.addEventListener("click", () => {
            let action = btn.dataset.action;
            let slug = btn.dataset.slug ? btn.dataset.slug : null;
            let url_post = getCategoriesUrl(action, slug)
            post_category_modal(url_post);
        });
    }
}

function getCategoriesUrl(action, slug = null){
    let url;
    switch (action){
        case "add":
            url = CATEGORIES_ADD_URL;
            break;
        case "edit":
            url = CATEGORIES_EDIT_URL + slug + "/";
            break;
        case "delete":
            url = CATEGORIES_DELETE_URL + slug + "/";
            break;
        default:
            url = "";
    }
    return url
}

function getCategoriesSelectedVideosSlugs(){
    // test slugs
    return ["0025-melancholymp4","0026-melancholymp4"];
}

function refreshCategoriesLinks(){
    fetch(CATEGORIES_LIST_URL, {
    method: "GET",
    headers: {
      "X-CSRFToken": "{{ csrf_token }}",
      "X-Requested-With": "XMLHttpRequest",
    },
    cache: "no-store",
  })
    .then((response) => response.text())
    .then((data) => {
      // Parse data into html and replace categories list
      let parser = new DOMParser();
      let html = parser.parseFromString(data, "text/html").body;
      categoriesListContainer.innerHTML = html.innerHTML;
      manageCategoriesLinks();
    })
    .catch(() => {
      showalert(gettext("An Error occurred while processing."), "alert-danger", "formalertdivbottomright");
    });
}

// Add event listeners on categories list buttons for the first time
manageCategoriesLinks();
