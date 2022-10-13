var infinite_waypoint;
var formCheckedInputs = [];
var regExGetOnlyChars = /([\D])/g;

function getInfiniteScrollWaypoint() {
  // Return Waypoint Infinite object to init/refresh the infinite scroll
  let infinite_loading = document.querySelector(".infinite-loading");
  return new Waypoint.Infinite({
    element: document.getElementById("videos_list"),
    onBeforePageLoad: function () {
      infinite_loading.style.display = "block";
    },
    onAfterPageLoad: function ($items) {
      infinite_loading.style.display = "none";
      let footer = document.querySelector("footer.static-pod");
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
          document.querySelector(
            "footer.static-pod .hidden-pod"
          ).style.display = "block";
          footer.setAttribute("style", "height:auto;");
          footer.classList.remove("fixed-bottom");
        }
      });
    },
  });
}

function replaceCountVideos(newCount) {
  // Replace count videos label (h1) with translation and plural
  var transVideoCount = newCount > 1 ? "videos found" : "video found";
  $("#video_count")[0].innerHTML = newCount + " " + gettext(transVideoCount);
}

function refreshVideosSearch(formCheckedInputs) {
  // Ajax request to refresh view with filtered video list

  return $.ajax({
    type: "GET",
    url: urlVideos,
    data: formCheckedInputs,
    dataType: "html",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
    },
    success: function (html, status) {
      if (infinite_waypoint) {
        infinite_waypoint.destroy();
      }
      $(".infinite-loading").remove();
      $(".infinite-more-link").remove();
      $("#videos_list").replaceWith(html);
      replaceCountVideos(countVideos);
      window.history.pushState({}, "", this.url);
    },
    error: function (result, status, error) {
      $("#videos_list").html(gettext("An Error occurred while processing."));
    },
  });
}

$(".form-check-input").change(function () {
  // Filter checkboxes change triggered event
  formCheckedInputs = [];
  $(".infinite-loading").show();
  $(".form-check-input input[type=checkbox]").attr("disabled", "true");
  $("#videos_list").html("");
  $("input[type=checkbox]:checked").each(function () {
    formCheckedInputs.push(this);
  });
  refreshVideosSearch(formCheckedInputs).done(function () {
    $(".infinite-loading").hide();
    infinite_waypoint = getInfiniteScrollWaypoint();
    $(".form-check-input input[type=checkbox]").removeAttr("disabled");
  });
});

// First launch of the infinite scroll
infinite_waypoint = getInfiniteScrollWaypoint();
