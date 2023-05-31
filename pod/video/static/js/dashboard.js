var dashboardFormContainer = document.getElementById("dashboardFormContainer");
var bulkUpdateActionSelect = document.getElementById("bulkUpdateActionSelect");
var confirmBulkUpdateBtn = document.getElementById("confirmBulkUpdateBtn");

// Add event listener on change Action Select
bulkUpdateActionSelect.addEventListener("change", function() {
    let action = bulkUpdateActionSelect.value;
    appendDynamicForm(action);
});

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

function appendDynamicForm(action){
    // Async request to get specific field to batch update
    fetch(urlDashboardForm, {
    method: 'POST',
    headers: {
      "X-CSRFToken": Cookies.get("csrftoken"),
      "X-Requested-With": "XMLHttpRequest",
    },
    dataType: "html",
    cache: "no-store",
    body: JSON.stringify({action:action}),
    })
    .then((response) => response.text())
    .then((data) => {
        let parser = new DOMParser();
        let html = parser.parseFromString(data, "text/html");
        dashboardFormContainer.innerHTML = data;
    })
    .catch((error) => {
        document.getElementById("videos_list").innerHTML = gettext(
            "An Error occurred while processing."
      );
    });
}

confirmBulkUpdateBtn.addEventListener("click", (e) => {
    e.preventDefault();
    bulk_update();
});
