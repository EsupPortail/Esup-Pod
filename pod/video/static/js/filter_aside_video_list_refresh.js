var infinite_waypoint;
var filterCheckedInputs = {};
var categoryChecked = null;
var regExGetOnlyChars = /([\D])/g;
var sort_column;
var sort_direction_asc = true;
var sort_direction_chars = ["8600","8599"];

function getInfiniteScrollWaypoint() {
  // Return Waypoint Infinite object to init/refresh the infinite scroll
  return new Waypoint.Infinite({
    element: $("#videos_list")[0],
    onBeforePageLoad: function () {
      $(".infinite-loading").show();
    },
    onAfterPageLoad: function ($items) {
      $(".infinite-loading").hide();
      feather.replace({ class: "align-bottom" });
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

function callAsyncListVideos(filterCheckedInputs) {
  // Ajax request to refresh view with filtered video list
  data = new FormData();
  sortInputsObject = {};
  sortInputsObject["sort_column"] = sortColumn;
  sortInputsObject["sort_direction_asc"]= sort_direction_asc;
  data.append("filterCheckedInputs",JSON.stringify(filterCheckedInputs));
  data.append("sortInputs",JSON.stringify(sortInputsObject));
  if(categoryChecked){
    data.append("categoryChecked",categoryChecked);
  }
  return $.ajax({
    type: "POST",
    url: urlVideos,
    data: data,
    processData: false,
    contentType: false,
    dataType: "html",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": Cookies.get("csrftoken"),
    },
    success: function (html, status) {
      if (infinite_waypoint) {
        infinite_waypoint.destroy();
      }
      $(".infinite-loading").remove();
      $(".infinite-more-link").remove();
      $("#videos_list").replaceWith(html);
      replaceCountVideos(countVideos);
    },
    error: function (result, status, error) {
      $("#videos_list").html(gettext("An Error occurred while processing "));
    },
  });
}

function refreshVideosSearch(){
  // Filter checkboxes change triggered event
  filterCheckedInputs = {};
  categoryChecked = null;
  $(".infinite-loading").show();
  $(".form-check-input input[type=checkbox]").attr("disabled", "true");
  $("#videos_list").html("");
  // Get all filter checkboxes
  $("input[type=checkbox]:checked.form-check-input").each(function(checkBox) {
    let checkBoxName = $(this).attr('name');
    let checkBoxValue = $(this).val();
    if(!filterCheckedInputs.hasOwnProperty(checkBoxName)){
        filterCheckedInputs[checkBoxName] = [];
    }
    filterCheckedInputs[checkBoxName].push(checkBoxValue);
  });
  // Get sort column
  sortColumn = $("#sort").val();
  // if USE_CATEGORY active filter with categories
  if(urlVideos == 'videos' && USE_CATEGORY && $(".categories_list_item.active")[0]){
    categoryChecked = $(".categories_list_item.active")[0].firstChild["dataset"]["slug"].split("-")[1];
  }
  // Ajax async call to get filtered videos
  callAsyncListVideos(filterCheckedInputs).done(function () {
    $(".infinite-loading").hide();
    infinite_waypoint = getInfiniteScrollWaypoint();
    $(".form-check-input input[type=checkbox]").removeAttr("disabled");
  });
}

// Add change trigger on filter inputs and column sort select
$(".form-check-input, .sort-select").change(function(e) {
  e.preventDefault();
  refreshVideosSearch();
});

// Add click trigger on adcending / descending sort button
$("#sort_direction_label").click(function(e) {
  e.preventDefault();
  sort_direction_asc = !sort_direction_asc;
  $("#sort_direction").prop("checked", !$("#sort_direction").prop("checked"));
  $("#sort_direction_label").html("&#"+(sort_direction_chars[+ sort_direction_asc]).toString());
  refreshVideosSearch();
});

// First launch of the infinite scroll
infinite_waypoint = getInfiniteScrollWaypoint();
