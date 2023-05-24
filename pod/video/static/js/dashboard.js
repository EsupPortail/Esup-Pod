var selectedVideos = ["0011-0", "0017-0"];

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
        "action" : "title",
        "value" : 1
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