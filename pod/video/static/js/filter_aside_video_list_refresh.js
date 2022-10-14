var infinite_waypoint;
var formCheckedInputs = [];
var regExGetOnlyChars = /([\D])/g;

// Return Waypoint Infinite object to init/refresh the infinite scroll
let infinite_loading = document.querySelector(".infinite-loading");

element = document.getElementById("videos_list");
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
    body.scrollHeight,
    body.offsetHeight,
    html.clientHeight,
    html.scrollHeight,
    html.offsetHeight
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
url = "";

document.addEventListener("DOMContentLoaded", (e) => {
  var infinite = new InfiniteLoader(url, onBeforePageLoad, onAfterPageLoad);
});

function replaceCountVideos(newCount) {
  // Replace count videos label (h1) with translation and plural
  var transVideoCount = newCount > 1 ? "videos found" : "video found";
  document.getElementById("video_count").innerHTML =
    newCount + " " + gettext(transVideoCount);
}

function refreshVideosSearch(formCheckedInputs) {
  // Ajax request to refresh view with filtered video list
  url = urlVideos;
  data = formCheckedInputs;

  fetch(url, {
    method: "GET",
    headers: {
      "X-CSRFToken": "{{ csrf_token }}",
    },
    data: formCheckedInputs,
    dataType: "html",
  })
    .then((response) => response.text())
    .then((data) => {
      // parse data into html and replace videos list
      // destroy waypoint id exists

      let html = new DOMParser().parseFromString(data, "text/html").body
        .firstChild;
      //document.querySelector(".infiniteloading").style.display = "none";
      //document.querySelector(".infinite-more-link").style.display = "none";
      document.getElementById("videos_list").innerHTML = "";
      replaceCountVideos(countVideos);
      window.history.pushState({}, "", this.url);
      hideInfiniteloading();
    })
    .catch((error) => {
      console.log(error);
      document.getElementById("videos_list").innerHTML = gettext(
        "An Error occurred while processing."
      );
    });
}
hideInfiniteloading = function () {
  //document.querySelector(".infiniteloading").style.display = "none";
  // get waypoint object
  document
    .querySelectorAll(".form-check-input input[type=checkbox]")
    .forEach((checkbox) => {
      checkbox.removeAttribute("disabled");
    });
};

document.querySelectorAll(".form-check-input").forEach((checkbox) => {
  checkbox.addEventListener("change", function () {
    // Filter checkboxes change triggered event
    console.log("checkbox changed");
    formCheckedInputs = [];
    document.querySelector(".infinite-loading").display = "block";
    document
      .querySelectorAll(".form-check-input input[type=checkbox]")
      .forEach((checkbox) => {
        checkbox.setAttribute("disable", "true");
      });

    document.getElementById("videos_list").innerHTML = "";
    document.querySelectorAll("input[type=checkbox]:checked").forEach((e) => {
      formCheckedInputs.push(e);
    });
    refreshVideosSearch(formCheckedInputs);
  });
});

// First launch of the infinite scroll
//infinite_waypoint = getInfiniteScrollWaypoint();
