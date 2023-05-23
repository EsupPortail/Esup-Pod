var selectedVideos = ["0011-melancholymp4", "0017-melancholymp4"];

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
        "selectedVideos" : selectedVideos,
        "action" : "action"
    })
  })
    .then((response) => response.json())
    .then((data) => {
    })
    .catch((error) => {
      console.log(error);
    });
}

bulk_update();