var infinite_waypoint;
var categoryChecked = null;
var sortDirectionAsc = false;
var sortDirectionChars = ["8600","8599"];
var urlVideosStr = urlVideos.toString().replaceAll("/","");
var filterSortForms = $(".filterSortForms");

function getInfiniteScrollWaypoint() {
  // Return Waypoint Infinite object to init/refresh the infinite scroll and pagination
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

function callAsyncListVideos() {
  // Ajax request to refresh view with filtered video list
  if(categoryChecked != null){
    urlVideos+="?category="+categoryChecked;
  }
  return $.get({
    url: urlVideos,
    data: filterSortForms.serialize(),
    processData: false,
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
      urlVideos = urlVideos.split("?")[0];
    },
    error: function (result, status, error) {
      $("#videos_list").html(gettext("An Error occurred while processing "));
    },
  });
}

function refreshVideosSearch(){
  // Filter checkboxes change triggered event
  categoryChecked = null;
  $(".infinite-loading").show();
  $("#videos_list").html("");
  $(".form-check-input input[type=checkbox]").attr("disabled", "true");
  // if USE_CATEGORY active filter with categories
  if(urlVideos !== 'videos' && USE_CATEGORY && $(".categories_list_item.active")[0]){
    categoryChecked = $(".categories_list_item.active")[0].firstChild["dataset"]["slug"].split("-")[1];
  }
  // Ajax async call to get filtered videos
  callAsyncListVideos().done(function () {
    replaceCountVideos(countVideos);
    localStorage.setItem(urlVideosStr+"LocalStorage",filterSortForms.serialize());
    $(".infinite-loading").hide();
    infinite_waypoint = getInfiniteScrollWaypoint();
    $(".form-check-input input[type=checkbox]").removeAttr("disabled");
    feather.replace();
  });
}

function replaceCountVideos(newCount) {
  // Replace count videos label (h1) with translation and plural
  var transVideoCount = newCount > 1 ? "videos found" : "video found";
  $("#video_count")[0].innerHTML = newCount + " " + gettext(transVideoCount);
}

function manageLocalStorage(){
    // Manage Local Storage for filters
    let filterLocalStorage = localStorage.getItem(urlVideosStr+"LocalStorage");
    if(filterLocalStorage !== null){
        filterLocalStorage = filterLocalStorage;
        let filterLocalStorageKeys = Object.keys(filterLocalStorage);
        // Loop on filter keys saved on local storage
        for (let i = 0; i < filterLocalStorageKeys.length; i++) {
            let key = filterLocalStorageKeys[i];
            let inputNames = filterLocalStorage[key];
            // Loop for each key filter values checked saved on local storage
            for (let j = 0; j < inputNames.length; j++) {
               let idSelector = "id"+inputNames[j]+"_"+key;
               // Manually check the checkbox found with id
               document.getElementById(idSelector).checked = true;
            }
        }
    }
    // Manage Local Storage for sort
    let sortLocalStorage = localStorage.getItem("sortLocalStorage"+urlVideosStr);
    if(sortLocalStorage !== null){
        sortLocalStorage = JSON.parse(sortLocalStorage);
        $("#sort").val(sortLocalStorage["sort_column"]);
        sortDirectionAsc = sortLocalStorage["sortDirectionAsc"];
        refreshSortDirectionChar();
    }
}

// Add change trigger on filter inputs and column sort select
$(".form-check-input, .sort-select").change(function(e) {
  e.preventDefault();
  refreshVideosSearch();
});

function toggleSortDirection(){
  sortDirectionAsc = !sortDirectionAsc;
  $("#sort_direction").prop("checked", !$("#sort_direction").prop("checked"));
  refreshSortDirectionChar();
}

function refreshSortDirectionChar(){
    $("#sort_direction_label").html("&#"+(sortDirectionChars[+ sortDirectionAsc]).toString());
}

// Add click trigger on ascending / descending sort button
$("#sort_direction_label").click(function(e) {
  e.preventDefault();
  toggleSortDirection();
  refreshVideosSearch();
});

// First launch of the infinite scroll
infinite_waypoint = getInfiniteScrollWaypoint();

// Get local storage and fill the form
manageLocalStorage();

// First launch of videos list refresh
refreshVideosSearch();

