var infinite_waypoint;
var categoryChecked = null;
var sortDirectionAsc = false;
var sortDirectionChars = ["8600","8599"];
var urlVideosStr = urlVideos.toString().replaceAll("/","");
var filterSortForms = $(".filterSortForms");
var loader = $("#loader_wrapper");

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
    cache: false,
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
      $("#video_list_content").html(html);
      urlVideos = urlVideos.split("?")[0];
    },
    error: function (result, status, error) {
      $("#videos_list").html(gettext("An Error occurred while processing "));
    },
  });
}

function refreshVideosSearch(){
  // Filter checkboxes change triggered event
  $(".infinite-loading").show();
  loader.addClass("show");
  categoryChecked = null;
  $(".form-check-input input[type=checkbox]").attr("disabled", "true");
  // if USE_CATEGORY active filter with categories
  if(urlVideos !== 'videos' && USE_CATEGORY && $(".categories_list_item.active")[0]){
    categoryChecked = $(".categories_list_item.active")[0].firstChild["dataset"]["slug"].split("-")[1];
  }
  // Ajax async call to get filtered videos
  callAsyncListVideos().done(function () {
    localStorage.setItem(urlVideosStr+"LocalStorage",filterSortForms.serialize());
    replaceCountVideos(countVideos);
    infinite_waypoint = getInfiniteScrollWaypoint();
    $(".form-check-input input[type=checkbox]").removeAttr("disabled");
    $(".infinite-loading").hide();
    loader.removeClass("show");
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
        let paramsLocalStorage = filterLocalStorage.split('&');
        for (let i = 0; i < paramsLocalStorage.length; i++) {
           let param = paramsLocalStorage[i].split('=');
           if(param[0] == "sort"){
                $("#sort").val(param[1]);
           }else if(param[0] == "cursus"){
               document.getElementById("cursus-"+param[1]).checked = true;
           }else{
               let idSelector = "id"+param[1]+"_"+param[0];
               // Manually check the checkbox found with id
               document.getElementById(idSelector).checked = true;
           }
        }
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

