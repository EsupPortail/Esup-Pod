var infinite_waypoint;
var formCheckedInputs = [];
var regExGetOnlyChars = /([\D])/g;

function getInfiniteScrollWaypoint() {
  // Return Waypoint Infinite object to init/refresh the infinite scroll
  return new Waypoint.Infinite({
    element: $("#videos_list")[0],
    onBeforePageLoad: function () {
      $(".infinite-loading").show();
    },
    onAfterPageLoad: function ($items) {
      $(".infinite-loading").hide();
      $("footer.static-pod").addClass("small");
      $("footer.static-pod").addClass("fixed-bottom");
      $("footer.static-pod").attr("style", "height:80px; overflow-y:auto");
      $("footer.static-pod .hidden-pod").css("display", "none");
      $(window).scroll(function () {
        if (
          $(window).height() + $(window).scrollTop() ===
          $(document).height()
        ) {
          $("footer.static-pod .hidden-pod").css("display", "block");
          $("footer.static-pod").attr("style", "height:auto;");
          $("footer.static-pod").removeClass("fixed-bottom");
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
