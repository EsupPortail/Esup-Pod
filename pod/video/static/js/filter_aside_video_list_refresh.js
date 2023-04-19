var infinite;
var checkedInputs = [];
var listUser;
var sortDirectionAsc = false;
var sortDirectionChars = ["8600","8599"];

let loader = document.querySelector(".lds-ring");
let infinite_loading = document.querySelector(".infinite-loading");
let ownerBox = document.getElementById("ownerbox");
let filterOwnerContainer = document.getElementById("collapseFilterOwner");

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
  // Erase list and enable loader
  document.getElementById("videos_list").innerHTML = "";
  loader.classList.add("show");
  url = getUrlForRefresh();
  // Async GET request wth parameters by fetch method
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
      replaceCountVideos(document.getElementById("videos_list").dataset.countvideos);
      nextPage = (document.getElementById("videos_list").getAttribute("nextPage") === 'true');
      window.history.pushState({}, "", url);
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
      // Finally re-enable inputs and dismiss loader
      disabledInputs(false);
      loader.classList.remove("show");
    });
}

// Return url with filter and sort parameters
function getUrlForRefresh(){
    let newUrl = window.location.pathname;
    // Add sort-related parameters
    newUrl += "?sort="+document.getElementById('sort').value+"&";
    if(sortDirectionAsc){
        newUrl += "sort_direction="+document.getElementById('sort_direction').value+"&";
    }
    // Add category checked if exists
    if(document.querySelectorAll(".categories_list_item.active").length !== 0){
        checkedCategory = document.querySelector(".categories_list_item.active").firstChild["dataset"]["slug"].split("-")[1];
        newUrl += "category="+checkedCategory+"&";
    }
    // Add all other parameters (filters)
    checkedInputs.forEach((input) => {
        newUrl += input.name + "=" + input.value + "&";
    });
    // Add page parameter
    newUrl += "page=";
    return newUrl;
}

// Add trigger event on change on inputs (filters, sort column and sort direction)
function setListenerChangeInputs(el){
    el.addEventListener('change', e => {
        checkedInputs = [];
        disabledInputs(true);
        document.querySelectorAll(
            "input[type=checkbox]:checked[class=form-check-input]"
        ).forEach((e) => {
            checkedInputs.push(e);
        });
        refreshVideosSearch();
    });
}

// Add event listener to search user input to create checkboxes
if (ownerBox) {
  ownerBox.addEventListener("input", (e) => {
    if (ownerBox.value && ownerBox.value.length > 2) {
      var searchTerm = ownerBox.value;
      getSearchListUsers(searchTerm).then((users) => {
      filterOwnerContainer.innerHTML = "";
        users.forEach((user) => {
            filterOwnerContainer.appendChild(createUserCheckBox(user));
            setListenerChangeInputs(document.getElementById("id"+user.username));
        });
      });
    }else{
        filterOwnerContainer.innerHTML = "";
    }
  });
}

// Create checkbox for user search
function createUserCheckBox(user){
    let div = document.createElement("div");
    div.classList.add("form-check");
    let checkbox = document.createElement("input");
    checkbox.classList.add("form-check-input");
    checkbox.type = "checkbox";
    checkbox.name = "owner";
    checkbox.value = user.username;
    checkbox.id = "id"+user.username;
    let label = document.createElement("label");
    label.classList.add("form-check-label");
    label.setAttribute("for","id"+user.username);
    label.innerHTML = user.first_name+" "+user.last_name;
    div.appendChild(checkbox);
    div.appendChild(label);
    return div;
}

// Add trigger event to manage reset of filters
document.getElementById("resetFilters").addEventListener('click', function() {
    checkedInputs = [];
    document.querySelectorAll("input[type=checkbox]:checked[class=form-check-input]").forEach((checkBox) => {
        checkBox.checked = false;
    });
    document.querySelectorAll("#filters .categories_list_item").forEach((c_p) => {
        c_p.classList.remove("active");
    });
    window.history.pushState("", "", window.location.pathname);
    refreshVideosSearch();
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

// Add event listener on inputs on launch
document.querySelectorAll('.form-check-input,#sort,#sort_direction').forEach(el => {
    setListenerChangeInputs(el);
});
