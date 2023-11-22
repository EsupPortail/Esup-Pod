var bulkUpdateActionSelect = document.getElementById("bulkUpdateActionSelect");
var confirmBulkUpdateBtn = document.getElementById("confirmBulkUpdateBtn");
var btnDisplayMode = document.querySelectorAll(".btn-dashboard-display-mode");
var action = "";
var value;

/**
 * Add change event listener on select action to get related inputs
 */
bulkUpdateActionSelect.addEventListener("change", function() {
    action = bulkUpdateActionSelect.value;
    appendDynamicForm(action);
    replaceSelectedCountVideos();
});

/**
 * Add click event listener on confirmation modal button to perform bulk update
 */
confirmBulkUpdateBtn.addEventListener("click", (e) => {
    e.preventDefault();
    bulkUpdate();
});

/**
 * Perform asynchronously bulk update on selected videos
 * @returns {Promise<void>}
 */
async function bulkUpdate() {

  // Init vars
  let formData = new FormData();
  let updateAction = action === "delete" || action === "transcript" ? action : "fields" ;
  let updateFields = [];

  // Set updated field(s)
  if (updateAction === "fields") {
      let formGroups = document.getElementById("dashboardForm").querySelectorAll(".form-group:not(.d-none)")
      Array.from(formGroups).forEach(formGroup => {
          let element = formGroup.querySelector(".form-control, .form-check-input, .form-select, input[name='thumbnail']");
          if (element.hasAttribute("multiple")) {
            formData.append(element.getAttribute("name"), element.value);
          } else {
            switch(element.type){
                case "checkbox":
                    value = element.checked
                    break;
                case "textarea":
                    value = CKEDITOR.instances[element.id].getData();
                    break;
                default:
                    value = document.getElementById("id_"+element.getAttribute("name")).value;
            }
            formData.append(element.getAttribute("name"), value);
          }
          updateFields.push(element.name);
      });
  }

  // Construct formData to send
  formData.append("selected_videos",JSON.stringify(getListSelectedVideos()));
  formData.append("update_fields",JSON.stringify(updateFields));
  formData.append("update_action",JSON.stringify(updateAction));

  // Post asynchronous request
  let response = await fetch(urlUpdateVideos, {
    method: "POST",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": csrftoken,
    },
    body:formData,
  });
    let result = await response.text();
    // Close modal and scroll to top
    bootstrap.Modal.getInstance(document.getElementById('modalConfirmBulkUpdate')).toggle();
    window.scroll({top: 0, left: 0, behavior: 'smooth'});
    // Parse result
    data = JSON.parse(result);
    let message = data["message"];
    let updatedVideos = data["updated_videos"];

    if (response.ok) {
        // Set selected videos with new slugs if changed during update
        selectedVideos = updatedVideos;
        showalert(message, "alert-success", "formalertdivbottomright");
        refreshVideosSearch();
    } else {
        // Manage field errors and global errors
        let errors = Array.from(data["fields_errors"]);
        if (errors.length > 0) {
            errors.forEach((error) => {
                let key = Object.keys(error)[0];
                let element = document.getElementById("id_"+key);
                if(element != null){
                    let message = error[key];
                    showDashboardFormError(element, message, "alert-danger");
                }
            });
        } else {
            showalert(message, "alert-danger", "formalertdivbottomright");
        }
    }
}

/**
 * Dynamically display input(s) for selected action
 * @param action
 */
function appendDynamicForm(action){
    // Append form group selected action
    let elements = document.querySelectorAll('.fieldset-dashboard, .form-group-dashboard');
    Array.from(elements).forEach((formGroup) => {
        formGroup.classList.add("d-none");
    });
    if (formFieldsets.includes(action)) {
        let fieldset = document.getElementById(action);
        fieldset.classList.remove("d-none");
        Array.from(fieldset.querySelectorAll(".form-group-dashboard")).forEach((formGroup) => {
            formGroup.classList.remove("d-none");
        });
    } else {
        let input = document.getElementById('id_'+action);
        if(input){
            input.closest(".form-group-dashboard").classList.remove("d-none");
        }
    }
}

/**
 * Change videos list display mode between "Grid" and "List"
 * @param display_mode
 */
function changeDisplayMode(display_mode){
    displayMode = display_mode;
    btnDisplayMode.forEach(e => e.classList.toggle("active"));
    refreshVideosSearch();
}

/**
 * Update list of selected videos for modal confirm display
 */
function updateModalConfirmSelectedVideos(){
    let str = "";
    Array.from(selectedVideos).forEach((video) => {
        str += "<li>"+video.split('-')[1]+"</li>";
    });
    bulkUpdateConfirmSelectedVideos.innerHTML = str;
}

/**
 * Show feedback message after bulk update
 * @param message
 * @param alertClass
 */
function showDashboardFormError(element, message, alertClass){
    let html = "<div class=\"alert "+alertClass+" alert-dismissible fade show my-2\" role=\"alert\">"+message+
        "<button type=\"button\" class=\"btn-close\" data-bs-dismiss=\"alert\" aria-label=\"Close\"></button></div>"
    element.insertAdjacentHTML("beforebegin", html);
}
