var selectedVideosCards;
var applyMultipleActionsBtn = document.getElementById("applyBulkUpdateBtn");
var resetSelectedVideosBtn = document.getElementById("resetSelectedVideosBtn");
var countSelectedVideosBadge = document.getElementById("countSelectedVideosBadge");
var countVideosModal = document.getElementById("countSelectedVideosModal");
var badgeToolTip = new bootstrap.Tooltip(applyMultipleActionsBtn, {
        title: "",
        html: true,
        placement: "bottom",
        delay: { "show": 0, "hide": 50 }
    });

function getListSelectedVideos(){
    selectedVideosCards = [];
    document.querySelectorAll(".infinite-item.selected").forEach((elt) => {
        selectedVideosCards.push(elt.dataset.slug);
    });
    return selectedVideosCards;
}

function setListSelectedVideos(){
    selectedVideosCards = [];
    document.querySelectorAll(".infinite-item.selected").forEach((elt) => {
        selectedVideosCards.push(elt.dataset.slug);
    });
}

function setSelectedVideos(){
    Array.from(selectedVideosCards).forEach((elt) => {
        let domElt = document.querySelector('#videos_list>.infinite-item[data-slug="'+elt+'"]');
        if(domElt && !domElt.classList.contains("selected")){
            if(!domElt.classList.contains("selected")){
                domElt.classList.add("selected");
            }
        }
    });
}

// Replace selected count videos label
function replaceSelectedCountVideos() {
  videos_selected = document.querySelectorAll(".infinite-item.selected");
  let newCount = videos_selected.length;
  countVideosModal.innerHTML = newCount;
  countSelectedVideosBadge.innerHTML = newCount+" vidéos";
  if(newCount > 0){
    let selected_slugs = []
    applyMultipleActionsBtn.removeAttribute('disabled');
    resetSelectedVideosBtn.removeAttribute('disabled');
    videos_selected.forEach((e) => {
        selected_slugs.push(e.dataset.slug.split('-')[1])
    });
    badgeToolTip._config.title = selected_slugs.join("<br>");
  }else{
    applyMultipleActionsBtn.setAttribute('disabled','');
    resetSelectedVideosBtn.setAttribute('disabled','');
  }
}

function toggleSelectedVideo(item){
    item.classList.toggle("selected");
    setListSelectedVideos();
    replaceSelectedCountVideos();
}

function clearSelectedVideo() {
    selectedVideosCards = []
    document.querySelectorAll(".infinite-item.selected").forEach((elt) => {
        elt.classList.remove("selected");
    });
    replaceSelectedCountVideos();
}

