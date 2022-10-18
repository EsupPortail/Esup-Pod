var infinite;
var formCheckedInputs = [];
var regExGetOnlyChars = /([\D])/g;

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
  infinite.removeLoader();
  infinite = null
  infinite = new InfiniteLoader(url, onBeforePageLoad, onAfterPageLoad, page = nextPage);
}


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
  url = url + "?" 
  data.forEach((input) => {
    url += input.name + "=" + input.value + "&";
  });
  url = url.slice(0, -1);
  
  console.log(url)


  
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
      // destroy waypoint id exists
     
      let html = new DOMParser().parseFromString(data, "text/html").body
        
        
      //document.querySelector(".infiniteloading").style.display = "none";
      //document.querySelector(".infinite-more-link").style.display = "none";
      document.getElementById("videos_list").outerHTML = html.querySelector("#videos_list").outerHTML;
      let nextPage = document.getElementById("videos_list").getAttribute("nextPage");
      
      replaceCountVideos(countVideos);
      window.history.pushState({}, "", this.url);
      hideInfiniteloading();
      if (nextPage) {
        pageNext = document.querySelector("a.infinite-more-link")
        if (url != urlVideos) 
          url = url + "?page=" + page;
        url = url + "&page=" + page;
        refreshInfiniteLoader(url, nextPage);
      }
      
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
        checkbox.setAttribute("disabled", "true");
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
if (next_page) {
  url = "/videos/?page=";
  infinite = new InfiniteLoader(url, onBeforePageLoad, onAfterPageLoad,next_page,  page = 2)
}


