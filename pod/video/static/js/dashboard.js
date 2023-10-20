var bulkUpdateActionSelect = document.getElementById("bulkUpdateActionSelect");
var confirmBulkUpdateBtn = document.getElementById("confirmBulkUpdateBtn");
var btnDisplayMode = document.querySelectorAll(".btn-dashboard-display-mode");
var action;
var value;

bulkUpdateActionSelect.addEventListener("change", function() {
    // Add event listener on change Action Select
    action = bulkUpdateActionSelect.value;
    appendDynamicForm(action);
});

async function bulk_update() {
  // Async POST request to bulk update videos
  let formData = new FormData();
  let update_fields = []
  if(action === "delete" || action === "transcript"){
      update_fields = [action];
  }else{
      let form_groups = document.getElementById("dashboardForm").querySelectorAll(".form-group:not(.d-none)")
      Array.from(form_groups).forEach(form_group => {
          let element = form_group.querySelector(".form-control, .form-check-input, .form-select, input[name='thumbnail']");
          if(element.hasAttribute("multiple")){
            formData.append(element.getAttribute("name"), element.value);
          }else{
            value = element.type === "checkbox" ? element.checked : document.getElementById("id_"+element.getAttribute("name")).value;
            formData.append(element.getAttribute("name"), value);
          }
          update_fields.push(element.name);
      });
  }

  formData.append("selected_videos",JSON.stringify(getListSelectedVideos()));
  formData.append("update_fields",JSON.stringify(update_fields));

  let response = await fetch(urlVideos, {
    method: "POST",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": csrftoken,
    },
    body:formData,
  });
    let result = await response.text();
    if(response.ok){
        data = JSON.parse(result);
        Array.from(data["updated_videos"]).forEach((v_slug) => {
            selectedVideosCards.push(v_slug);
        });
        showalert(gettext("The changes have been saved."), "alert-success");
        refreshVideosSearch();
    }else{
        showalert(JSON.parse(result)["error"],"alert-danger");
    }
    bootstrap.Modal.getInstance(document.getElementById('modalConfirmBulkUpdate')).toggle();
}

function appendDynamicForm(action){
    // Append form group selected action
    let elements = document.querySelectorAll('.fieldset-dashboard, .form-group-dashboard');
    Array.from(elements).forEach((form_group) => {
        form_group.classList.add("d-none");
    });
    if(formFieldsets.includes(action)){
        let fieldset = document.getElementById(action);
        fieldset.classList.remove("d-none");
        Array.from(fieldset.querySelectorAll(".form-group-dashboard")).forEach((form_group) => {
            form_group.classList.remove("d-none");
        });
    }else{
        let input = document.getElementById('id_'+action);
        if(input){
            input.closest(".form-group-dashboard").classList.remove("d-none");
        }
    }
}

function changeDisplayMode(display_mode){
    // Change display mode between grid and list
    displayMode = display_mode;
    btnDisplayMode.forEach(e => e.classList.toggle("active"));
    refreshVideosSearch();
}

confirmBulkUpdateBtn.addEventListener("click", (e) => {
    // Add event listener to perform bulk update after confirmation modal
    e.preventDefault();
    bulk_update();
});
