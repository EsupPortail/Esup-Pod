var infinite_waypoint;
var categoryChecked = null;
var sortDirectionAsc = false;
var sortDirectionChars = ["8600","8599"];
var urlVideosStr = urlVideos.toString().replaceAll("/","");
var filterSortForms = $(".filterSortForms");
var loader = $("#loader_wrapper");

// Return Waypoint Infinite object to init/refresh the infinite scroll and pagination gesture
function getInfiniteScrollWaypoint() {
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

// Prepare front for refresh videos list
function refreshVideosSearch(){
  categoryChecked = null;
  // Start treatment -> show loader and Loading text
  $(".infinite-loading").show();
  loader.addClass("show");
  // Disable checkboxes during refresh
  $(".form-check-input input[type=checkbox]").attr("disabled", "true");
  // Ajax call to get filtered videos
  callAsyncListVideos().done(function () {
    localStorage.setItem(urlVideosStr+"LocalStorage",filterSortForms.serialize());
    replaceCountVideos(countVideos);
    infinite_waypoint = getInfiniteScrollWaypoint();
    $(".form-check-input input[type=checkbox]").removeAttr("disabled");
    $(".infinite-loading").hide();
    loader.removeClass("show");
    // reload feather icons generation
    feather.replace();
  });
}

// Ajax request to refresh view with filtered video list
function callAsyncListVideos() {
  // if category is checked add param to url
  if(urlVideos !== 'videos' && USE_CATEGORY && $(".categories_list_item.active").length){
    categoryChecked = document.querySelector(".categories_list_item.active").firstChild["dataset"]["slug"].split("-")[1];
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
      $("#video_list_content").html(html);
      urlVideos = urlVideos.split("?")[0];
      window.history.pushState({},"Title",window.location.origin+fullPath);
    },
    error: function (result, status, error) {
      $("#videos_list").html(gettext("An Error occurred while processing "));
    },
  });
}

// Replace count videos label (h1) with translation and plural
function replaceCountVideos(newCount) {
  var transVideoCount = newCount > 1 ? "videos found" : "video found";
  document.getElementById("video_count").innerHTML = newCount + " " + gettext(transVideoCount);
}

// Add click listener for filters reset
$("#resetFilters").click(function() {
  $(".form-check-input:checkbox:checked:not(#sort_direction)").each(function(){
    this.checked = false;
  });
  document.querySelectorAll("#filters .categories_list_item").forEach((c_p) => {
    c_p.classList.remove("active");
  });
  categoryChecked = null;
  refreshVideosSearch();
});

// Add change listener on filter and sort inputs to launch refresh
$(".form-check-input, .sort-select").change(function(e) {
  e.preventDefault();
  refreshVideosSearch();
});

// Add click listener on ascending/descending sort button to launch refresh
$("#sort_direction_label").click(function(e) {
  e.preventDefault();
  toggleSortDirection();
  refreshVideosSearch();
});

// Toggle direction of sort and refresh videos list
function toggleSortDirection(){
  sortDirectionAsc = !sortDirectionAsc;
  $("#sort_direction").prop("checked", !$("#sort_direction").prop("checked"));
  updateSortDirectionChar();
}

// Update arrow char of ascending or descending sort order
function updateSortDirectionChar(){
  $("#sort_direction_label").html("&#"+(sortDirectionChars[+ sortDirectionAsc]).toString());
}

// Manage Local Storage for filters
function manageLocalStorage(){
    let urlBase = window.location.href.split(window.location.origin)[1];
    let filterLocalStorage = localStorage.getItem(urlVideosStr+"LocalStorage");
    // Apply local storage only if url is base (without parameters)
    if(urlBase == urlVideos && filterLocalStorage !== null){
        let paramsLocalStorage = filterLocalStorage.split('&');
        // Get all parameters by key/value pairs
        for (let i = 0; i < paramsLocalStorage.length; i++) {
           let param = paramsLocalStorage[i].split('=');
           if(param[0] == "sort"){
                $("#sort").val(param[1]);
           }else if(param[0] == "sort_direction"){
               sortDirectionAsc = true;
               updateSortDirectionChar();
           }else if(param[0] == "cursus"){
               document.getElementById("cursus-"+param[1]).checked = true;
           }else{
               let idSelector = "id"+param[1]+"_"+param[0];
               // Manually check the checkbox found with id
               if(document.getElementById(idSelector)!== null){
                    document.getElementById(idSelector).checked = true;
               }
           }
        }
    }
}

// First launch of the infinite scroll
infinite_waypoint = getInfiniteScrollWaypoint();

// Get local storage and fill the form
manageLocalStorage();

// First launch of videos list refresh
refreshVideosSearch();

