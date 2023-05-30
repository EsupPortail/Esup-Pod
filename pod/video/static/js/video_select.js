var selectedVideosCards = [];
var applyMultipleActionsBtn = document.getElementById("applyBulkUpdateBtn");
var countVideosSelectedBadge = document.getElementById("countSelectedVideosBadge");
var countVideosModal = document.getElementById("countSelectedVideosModal");

function getListSelectedVideos(){
    selectedVideosCards = [];
    document.querySelectorAll(".infinite-item.selected").forEach((elt) => {
        selectedVideosCards.push(elt.dataset.slug);
    });
    return selectedVideosCards;
}

addEventSelectOnVideos();

// Replace selected count videos label
function replaceSelectedCountVideos() {
  videos_selected = document.querySelectorAll(".selected");
  let newCount = videos_selected.length;
  countVideosModal.innerHTML = newCount;
  countVideosSelectedBadge.innerHTML = newCount+" vidéos";
  if(newCount > 0){
    applyMultipleActionsBtn.removeAttribute('disabled');
  }else{
    applyMultipleActionsBtn.setAttribute('disabled','');
  }
}

function addEventSelectOnVideos(){
    var videos_to_display = document.getElementsByClassName("infinite-item");
    Array.from(videos_to_display).forEach((v) => {
        v.addEventListener("click", function() {
            v.classList.toggle("selected");
            replaceSelectedCountVideos();
        });
    });
}
