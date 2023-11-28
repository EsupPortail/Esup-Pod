var selectedVideos;
var applyMultipleActionsBtn = document.getElementById("applyBulkUpdateBtn");
var resetSelectedVideosBtn = document.getElementById("resetSelectedVideosBtn");
var countSelectedVideosBadge = document.getElementById("countSelectedVideosBadge");
var badgeToolTip = new bootstrap.Tooltip(applyMultipleActionsBtn, {
        title: "",
        html: true,
        placement: "bottom",
        delay: { "show": 0, "hide": 50 }
    });

/**
 * Get list of selected videos (cards or list-items selected by user) based on class selected
 * @returns {*[videos]}
 */
function getListSelectedVideos(){
    selectedVideos = [];
    document.querySelectorAll(".infinite-item.selected").forEach((elt) => {
        selectedVideos.push(elt.dataset.slug);
    });
    return selectedVideos;
}

/**
 * Set shared/global variable selectedVideos with selected videos based on class selected
 */
function setListSelectedVideos(){
    selectedVideos = [];
    document.querySelectorAll(".infinite-item.selected").forEach((elt) => {
        selectedVideos.push(elt.dataset.slug);
    });
}

/**
 * Set directly selected videos on interface to improve user experience
 */
function setSelectedVideos(){
    Array.from(selectedVideos).forEach((elt) => {
        let domElt = document.querySelector('#videos_list .infinite-item[data-slug="'+elt+'"]');
        if(domElt && !domElt.classList.contains("selected")){
            if(!domElt.classList.contains("selected")){
                domElt.classList.add("selected");
            }
        }
    });
}

/**
 * Replace count of selected videos (count label in "Apply" bulk update's badge)
 */
function replaceSelectedCountVideos() {
  videos_selected = getListSelectedVideos();
  let selected_slugs = []
  let newCount = videos_selected.length;
  let transVideoCount = newCount > 1 ? "videos" : "video";
  countSelectedVideosBadge.innerHTML = newCount + " " + gettext(transVideoCount);

  manageDisableBtn(applyMultipleActionsBtn, newCount > 0 && action.length !== 0);
  manageDisableBtn(resetSelectedVideosBtn, newCount > 0);
  videos_selected.forEach((v) => {
      selected_slugs.push(v.split('-')[1])
  });
  badgeToolTip._config.title = selected_slugs.join("<br>");
}

/**
 * Toggle class selected for video cards or list-item, avoid select a video when click on links
 * @param item
 */
function toggleSelectedVideo(item){
    // Prevent item to select if link is clicked
    if(
        event.target.tagName === "A" ||
        event.target.tagName === "BUTTON" ||
        event.target.classList.contains("card-footer-link-i") ||
        event.target.classList.contains("more-actions-row-i")) {
        return;
    }
    item.classList.toggle("selected");
    setListSelectedVideos();
    replaceSelectedCountVideos();
}

/**
 * Clear videos selection : deselect all videos, reset badge count
 */
function clearSelectedVideo() {
    selectedVideos = []
    document.querySelectorAll(".infinite-item.selected").forEach((elt) => {
        elt.classList.remove("selected");
    });
    replaceSelectedCountVideos();
}

/**
 * Get list of selected videos slugs (HTML li formated) for modal confirm display
 */
function getHtmlListSelectedVideosSlugs(){
    let str = "";
    Array.from(selectedVideos).forEach((video) => {
        str += "<li>"+video.split('-')[1]+"</li>";
    });
    return str;
}
