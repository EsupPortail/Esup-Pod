/**
 * @file Esup-Pod functions for dashboard view.
 * @since 3.5.0
 */

// Read-only globals defined in video_select.js
/*
  global replaceSelectedCountVideos selectedVideos getHTMLBadgesSelectedTitles resetDashboardElements
*/

// Read-only globals defined in filter_aside_video_list_refresh.js
/*
  global refreshVideosSearch
*/

// Read-only globals defined in dashboard.html
/*
  global urlUpdateVideos csrftoken formFieldsets displayMode
*/

// Read-only globals defined in video_select.js
/*
  global selectedVideos
*/

/* exported dashboardActionReset */

var bulkUpdateActionSelect = document.getElementById(
  "bulk-update-action-select",
);
var applyBulkUpdateBtn = document.getElementById("applyBulkUpdateBtn");
var resetDashboardElementsBtn = document.getElementById(
  "reset-dashboard-elements-btn",
);
var modalLoader = document.getElementById("bulkUpdateLoader");
var modal = document.getElementById("modalBulkUpdate");
var confirmModalBtn = document.getElementById("confirmModalBtn");
var cancelModalBtn = document.getElementById("cancelModalBtn");
var btnDisplayMode = document.querySelectorAll(".btn-dashboard-display-mode");
var dashboardAction = "";
var dashboardValue;
selectedVideos[videosListContainerId] = [];

/**
 * Add change event listener on select action to get related inputs
 */
bulkUpdateActionSelect.addEventListener("change", function () {
  dashboardAction = bulkUpdateActionSelect.value;
  appendDynamicForm(dashboardAction);
  replaceSelectedCountVideos(videosListContainerId);
});

/**
 * Add click event listener on apply button to build and open confirm modal
 */
applyBulkUpdateBtn.addEventListener("click", () => {
  let selectedCount = selectedVideos[videosListContainerId].length;
  let modalEditionConfirmStr = ngettext(
    "Please confirm the editing of the following video:",
    "Please confirm the editing of the following videos:",
    selectedCount,
  );
  let modalDeleteConfirmStr = ngettext(
    "Please confirm the deletion of the following video:",
    "Please confirm the deletion of the following videos:",
    selectedCount,
  );
  let modalConfirmStr;
  if (dashboardAction === "delete") {
    modalConfirmStr = modalDeleteConfirmStr;
  } else {
    modalConfirmStr = modalEditionConfirmStr;
  }

  modalConfirmStr = interpolate(
    modalConfirmStr,
    { count: selectedCount },
    true,
  );
  modal.querySelector(".modal-body").innerHTML =
    "<p>" +
    modalConfirmStr +
    "</p>" +
    getHTMLBadgesSelectedTitles(videosListContainerId);
});

/**
 * Add click event listener on confirmation modal button to perform bulk update
 */
confirmModalBtn.addEventListener("click", (e) => {
  e.preventDefault();
  showLoader(modalLoader, true);
  manageDisableBtn(cancelModalBtn, false);
  manageDisableBtn(confirmModalBtn, false);
  modalLoader.focus();
  bulkUpdate().then(() => {
    showLoader(modalLoader, false);
    bootstrap.Modal.getInstance(modal).toggle();
    manageDisableBtn(cancelModalBtn, true);
    manageDisableBtn(confirmModalBtn, true);
  });
  resetDashboardElements();
});

/**
 * Reset action and value of dashboard form elements when reset button is clicked.
 **/
function dashboardActionReset() {
  dashboardAction = "";
  dashboardValue = "";
  bulkUpdateActionSelect.value = "";
  bulkUpdateActionSelect.dispatchEvent(new Event("change"));
}

/**
 * Perform asynchronously bulk update on selected videos
 * @returns {Promise<void>}
 */
async function bulkUpdate() {
  // Init vars
  let formData = new FormData();
  let updateAction = dashboardAction === "delete" ? dashboardAction : "fields";
  let updateFields = [];
  let message = "";

  // Set updated field(s)
  if (updateAction === "fields") {
    let formGroups = document
      .getElementById("dashboardForm")
      .querySelectorAll(".form-group:not(.d-none)");
    Array.from(formGroups).forEach((formGroup) => {
      let element = formGroup.querySelector(
        ".form-control, .form-check-input, .form-select, input[name='thumbnail']",
      );
      if (element.hasAttribute("multiple")) {
        formData.append(element.getAttribute("name"), element.value);
      } else {
        switch (element.type) {
          case "checkbox":
            dashboardValue = element.checked;
            break;
          case "textarea":
            dashboardValue = CKEDITOR.instances[element.id].getData();
            break;
          default:
            dashboardValue = document.getElementById(
              "id_" + element.getAttribute("name"),
            ).value;
        }
        formData.append(element.getAttribute("name"), dashboardValue);
      }
      updateFields.push(element.name);
    });
  }

  // Remove unecessaries fields.
  if (updateFields.includes("channel") && updateFields.includes("theme")) {
    if (formData.get("channel") != "" && formData.get("theme") == "") {
      updateFields.pop("theme");
      formData.delete("theme");
    }
  }

  // Construct formData to send
  formData.append(
    "selected_videos",
    JSON.stringify(selectedVideos[videosListContainerId]),
  );
  formData.append("update_fields", JSON.stringify(updateFields));
  formData.append("update_action", updateAction);

  // Post asynchronous request
  let response = await fetch(urlUpdateVideos, {
    method: "POST",
    headers: {
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": csrftoken,
    },
    body: formData,
  });
  let result = await response.text();

  // Parse result
  let data = JSON.parse(result);
  message = data["message"];

  if (response.ok) {
    // Set selected videos with new slugs if changed during update
    selectedVideos[videosListContainerId] = data["updated_videos"];
    showalert(message, "alert-success", "form-alert-div-bottom-right");
    refreshVideosSearch();
    replaceSelectedCountVideos(videosListContainerId);
  } else {
    // Manage field errors and global errors
    let errors = Array.from(data["fields_errors"]);
    if (errors.length > 0) {
      errors.forEach((error) => {
        let key = Object.keys(error)[0];
        let element = document.getElementById("id_" + key);
        if (element != null) {
          let message = error[key];
          showDashboardFormError(element, message, "alert-danger");
        }
      });
      window.scroll({ top: 0, left: 0, behavior: "smooth" });
    } else {
      showalert(message, "alert-danger", "form-alert-div-bottom-right");
    }
  }
}

/**
 * Dynamically display input(s) for selected action
 * @param action
 */
function appendDynamicForm(action) {
  // Append form group selected action
  let elements = document.querySelectorAll(
    ".fieldset-dashboard, .form-group-dashboard",
  );
  Array.from(elements).forEach((formGroup) => {
    formGroup.classList.add("d-none");
  });
  if (formFieldsets.includes(action)) {
    let fieldset = document.getElementById(action);
    fieldset.classList.remove("d-none");
    Array.from(fieldset.querySelectorAll(".form-group-dashboard")).forEach(
      (formGroup) => {
        formGroup.classList.remove("d-none");
      },
    );
  } else {
    let input = document.getElementById("id_" + action);
    if (input) {
      input.closest(".form-group-dashboard").classList.remove("d-none");
    }
  }
}

/**
 * Change videos list display mode between "Grid" and "List"
 * @param display_mode
 */
function changeDisplayMode(display_mode) {
  displayMode = display_mode;
  btnDisplayMode.forEach((e) => e.classList.toggle("active"));
  refreshVideosSearch();
}

/**
 * Show feedback message after bulk update
 * @param element
 * @param message
 * @param alertClass
 */
function showDashboardFormError(element, message, alertClass) {
  let html =
    '<div class="alert ' +
    alertClass +
    ' alert-dismissible fade show my-2" role="alert">' +
    message +
    '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="' +
    gettext("Close") +
    '"></button></div>';
  element.insertAdjacentHTML("beforebegin", html);
}
