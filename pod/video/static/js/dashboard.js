var confirmBulkUpdateBtn = document.getElementById("confirmBulkUpdateBtn");

function bulk_update() {
  // Async POST request to bulk update
  fetch(urlVideosUpdate, {
    method: "POST",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": csrftoken,
      "Accept": "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
        "selectedVideos" : getListSelectedVideos(),
        "action" : "type",
        "value" : 4
    })
  })
    .then((response) => response.json())
    .then((data) => {
    })
    .catch((error) => {
      console.log(error);
    });
}

confirmBulkUpdateBtn.addEventListener("click", (e) => {
    e.preventDefault();
    bulk_update();
});
