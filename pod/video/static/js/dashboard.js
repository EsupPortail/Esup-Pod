var dashboardFormContainer = document.getElementById("dashboardFormContainer");
var dashboardForm = document.getElementById("dashboardForm");
var bulkUpdateActionSelect = document.getElementById("bulkUpdateActionSelect");
var confirmBulkUpdateBtn = document.getElementById("confirmBulkUpdateBtn");
var action;
var value;

bulkUpdateActionSelect.addEventListener("change", function() {
    // Add event listener on change Action Select
    action = bulkUpdateActionSelect.value;
    if(action !== "delete" && action != ""){
        appendDynamicForm(action);
    }
});

function bulk_update() {
  // Async POST request to bulk update videos
  let element = document.getElementById("id_"+action);
  if(element.hasAttribute("multiple")){
    value = Array.from(element.querySelectorAll("option:checked"),e => e.value);
  }else{
    value = document.getElementById("id_"+action).value;
  }

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
        "action" : action,
        "value" : value
    })
  })
    .then((response) => response.json())
    .then((data) => {
    })
    .catch((error) => {
      document.getElementById("videos_list").innerHTML = gettext(
            "An Error occurred while processing."
      );
    });
}

function appendDynamicForm(action){
    // Append form group selected action
    let form_groups = document.querySelectorAll('.form-group');
    Array.from(form_groups).forEach((form_group) => {
        form_group.classList.add("d-none");
    });
    let input = document.getElementById('id_'+action);
    input.closest(".form-group").classList.remove("d-none");
}

confirmBulkUpdateBtn.addEventListener("click", (e) => {
    // Add event listener to perform bulk update after confirmation modal
    e.preventDefault();
    bulk_update();
});
