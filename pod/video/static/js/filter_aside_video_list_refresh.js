var url;
var infinite;
var formCheckedInputs = [];
var regExGetOnlyChars = /([\D])/g;
var sortDirectionAsc = false;
var sortDirectionChars = ["8600","8599"];
// Return Waypoint Infinite object to init/refresh the infinite scroll
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

function replaceCountVideos(newCount) {
  // Replace count videos label (h1) with translation and plural
  var transVideoCount = newCount > 1 ? "videos found" : "video found";
  document.getElementById("video_count").innerHTML =
    newCount + " " + gettext(transVideoCount);
}

function refreshVideosSearch() {
  url = getUrlForRefresh();
  // Ajax request to refresh view with filtered video list
  if (getNextPage()) {
    pageNext = document
        .querySelector("a.infinite-more-link")
        .getAttribute("nextPageNumber");
  }

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
      document.getElementById("videos_list").outerHTML = html.outerHTML;
      //document.querySelector(".infiniteloading").style.display = "none";
      //document.querySelector(".infinite-more-link").style.display = "none";
      replaceCountVideos(
        document.getElementById("videos_list").dataset.countvideos
      );
      window.history.pushState({}, "", this.url);
      hideInfiniteloading();
      if (getNextPage()) {
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
    });
}

function getUrlForRefresh(){
    url = window.location.pathname;
    data = formCheckedInputs;
    url += "?sort="+document.getElementById('sort').value+"&";
    if(sortDirectionAsc){
        url += "sort_direction="+document.getElementById('sort_direction').value+"&";
    }
    data.forEach((input) => {
        url += input.name + "=" + input.value + "&";
    });
    url += "page=";
    return url;
}

function getNextPage(){
    let nextPage = document
        .getElementById("videos_list")
        .getAttribute("nextPage");
    return nextPage;
}

hideInfiniteloading = function () {
  // get waypoint object
  document
    .querySelectorAll("input[type=checkbox][class=form-check-input]")
    .forEach((checkbox) => {
      checkbox.removeAttribute("disabled");
    });
};

document.querySelectorAll('.form-check-input,#sort,#sort_direction').forEach(el =>{
    el.addEventListener('change', e => {
        formCheckedInputs = [];
        document.querySelector(".infinite-loading").display = "block";
        document
            .querySelectorAll("input[type=checkbox][class=form-check-input]")
            .forEach((checkbox) => {
              checkbox.setAttribute("disabled", "true");
            });
        document.querySelectorAll(
            "input[type=checkbox]:checked[class=form-check-input]"
        ).forEach((e) => {
            formCheckedInputs.push(e);
        });
        document.getElementById("videos_list").innerHTML = "";
        this.refreshVideosSearch();
    });
});

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

// First launch of the infinite scroll
infinite = new InfiniteLoader(
    getUrlForRefresh(),
    onBeforePageLoad,
    onAfterPageLoad,
    nextPage,
    (page = 2)
);
