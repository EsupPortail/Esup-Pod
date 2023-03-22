var url;
var infinite;
var formCheckedInputs = [];
var regExGetOnlyChars = /([\D])/g;
var sortDirectionAsc = false;
var sortDirectionChars = ["8600","8599"];

let loader = document.querySelector(".loader_wrapper");
let infinite_loading = document.querySelector(".infinite-loading");

onBeforePageLoad = function () {
  infinite_loading.style.display = "block";
};
onAfterPageLoad = function () {
  infinite_loading.style.display = "none";
  let footer = document.querySelector("footer.static-pod");
  if (!footer) return;
  footer.classList.add("small");
  footer.classList.add("fixed-bottom");
  footer.setAttribute("style", "height:80px; overflow-y:auto");
  var docHeight = Math.max(
    document.body.scrollHeight,
    document.body.offsetHeight,
    document.clientHeight,
    document.scrollHeight,
    document.offsetHeight
  );
  document.querySelector("footer.static-pod .hidden-pod").style.display =
    "none";
  window.addEventListener("scroll", function () {
    if (window.innerHeight + window.scrollTop() === docHeight) {
      document.querySelector("footer.static-pod .hidden-pod").style.display =
        "block";
      footer.setAttribute("style", "height:auto;");
      footer.classList.remove("fixed-bottom");
    }
  });
};

function refreshInfiniteLoader(url, nextPage) {
  if(infinite !== undefined){
    infinite.removeLoader();
  }
  infinite = null;
  infinite = new InfiniteLoader(
    url,
    onBeforePageLoad,
    onAfterPageLoad,
    (page = nextPage)
  );
}

// Replace count videos label (h1) with translation and plural
function replaceCountVideos(newCount) {
  var transVideoCount = newCount > 1 ? "videos found" : "video found";
  document.getElementById("video_count").innerHTML =
    newCount + " " + gettext(transVideoCount);
}

// Async request to refresh view with filtered and sorted video list
function refreshVideosSearch() {
  loader.classList.add("show");
  url = getUrlForRefresh();

  fetch(url, {
    method: "GET",
    headers: {
      "X-CSRFToken": "{{ csrf_token }}",
      "X-Requested-With": "XMLHttpRequest",
    },
    dataType: "html",
  })
    .then((response) => response.text())
    .then((data) => {
      // parse data into html and replace videos list
      let parser = new DOMParser();
      let html = parser.parseFromString(data, "text/html").body;
      document.getElementById("videos_list").outerHTML = html.innerHTML;
      this.replaceCountVideos(document.getElementById("videos_list").dataset.countvideos);
      nextPage = (document.getElementById("videos_list").getAttribute("nextPage") === 'true');
      window.history.pushState({}, "", this.url);
      if (nextPage) {
        pageNext = document
          .querySelector("a.infinite-more-link")
          .getAttribute("nextPageNumber");
        refreshInfiniteLoader(url, pageNext);
      }
    })
    .catch((error) => {
      document.getElementById("videos_list").innerHTML = gettext(
        "An Error occurred while processing."
      );
    })
    .finally(() => {
      this.disabledInputs(false);
      loader.classList.remove("show");
    });
}

// Return url with filter and sort parameters
function getUrlForRefresh(){
    url = window.location.pathname;
    data = formCheckedInputs;
    url += "?sort="+document.getElementById('sort').value+"&";
    if(sortDirectionAsc){
        url += "sort_direction="+document.getElementById('sort_direction').value+"&";
    }
    if(document.querySelectorAll(".categories_list_item.active").length !== 0){
        categoryChecked = document.querySelector(".categories_list_item.active").firstChild["dataset"]["slug"].split("-")[1];
        url += "category="+categoryChecked+"&";
    }
    data.forEach((input) => {
        url += input.name + "=" + input.value + "&";
    });
    url += "page=";
    return url;
}

// Add trigger event on change on inputs (filters, sort column and sort direction)
document.querySelectorAll('.form-check-input,#sort,#sort_direction').forEach(el =>{
    el.addEventListener('change', e => {
        formCheckedInputs = [];
        this.disabledInputs(true);
        document.querySelectorAll(
            "input[type=checkbox]:checked[class=form-check-input]"
        ).forEach((e) => {
            formCheckedInputs.push(e);
        });
        this.refreshVideosSearch();
    });
});

// Add trigger event to manage sort direction
document.getElementById("sort_direction_label").addEventListener('click', function(e) {
    e.preventDefault();
    toggleSortDirection();
    refreshVideosSearch();
});

// Update arrow char of ascending or descending sort order
function updateSortDirectionChar(){
  document.getElementById("sort_direction_label").innerHTML = "&#"+(sortDirectionChars[+ sortDirectionAsc]).toString();
}

// Toggle direction of sort and refresh videos list
function toggleSortDirection(){
  sortDirectionAsc = !sortDirectionAsc;
  document.getElementById("sort_direction").checked = !document.getElementById("sort_direction").checked;
  updateSortDirectionChar();
}

// Enable / Disable toggle inputs to prevent user actions during loading
function disabledInputs(value){
    document
        .querySelectorAll("input[type=checkbox][class=form-check-input]")
        .forEach((checkbox) => {
            checkbox.disabled = value;
        });
}

// First launch of the infinite scroll
infinite = new InfiniteLoader(
    getUrlForRefresh(),
    onBeforePageLoad,
    onAfterPageLoad,
    nextPage,
    (page = 2)
);
