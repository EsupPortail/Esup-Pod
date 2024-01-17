/**
 * @file Esup-Pod functions for dashboard view.
 * @since 3.5.0
 */
var bulkUpdateActionSelect = document.getElementById("bulkUpdateActionSelect");
var applyBulkUpdateBtn = document.getElementById("applyBulkUpdateBtn");
var modalLoader = document.getElementById("bulkUpdateLoader");
var modal = document.getElementById("modalBulkUpdate");
var confirmModalBtn = document.getElementById("confirmModalBtn");
var cancelModalBtn = document.getElementById("cancelModalBtn");
var btnDisplayMode = document.querySelectorAll(".btn-dashboard-display-mode");
var action = "";
var value;

/**
 * Add change event listener on select action to get related inputs
 */
bulkUpdateActionSelect.addEventListener("change", function () {
  action = bulkUpdateActionSelect.value;
  appendDynamicForm(action);
  replaceSelectedCountVideos();
});

/**
 * Add click event listener on apply button to build and open confirm modal
 */
applyBulkUpdateBtn.addEventListener("click", (e) => {
  let selectedCount = selectedVideos.length;
  let modalConfirmStr = ngettext(
    `Please confirm the editing of the following video:`,
    `Please confirm the editing of the following videos:`,
    selectedCount,
  );
  modalConfirmStr = interpolate(
    modalConfirmStr,
    { count: selectedCount },
    true,
  );
  modal.querySelector(".modal-body").innerHTML =
    "<p>" + modalConfirmStr + "</p>" + getHTMLBadgesSelectedTitles();
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
});

/**
 * Perform asynchronously bulk update on selected videos
 * @returns {Promise<void>}
 */
async function bulkUpdate() {
  // Init vars
  let formData = new FormData();
  let updateAction = action === "delete" ? action : "fields";
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
            value = element.checked;
            break;
          case "textarea":
            value = CKEDITOR.instances[element.id].getData();
            break;
          default:
            value = document.getElementById(
              "id_" + element.getAttribute("name"),
            ).value;
        }
        formData.append(element.getAttribute("name"), value);
      }
      updateFields.push(element.name);
    });
  }

  // Construct formData to send
  formData.append("selected_videos", JSON.stringify(selectedVideos));
  formData.append("update_fields", JSON.stringify(updateFields));
  formData.append("update_action", JSON.stringify(updateAction));

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
  data = JSON.parse(result);
  message = data["message"];

  if (response.ok) {
    // Set selected videos with new slugs if changed during update
    selectedVideos = data["updated_videos"];
    showalert(message, "alert-success", "formalertdivbottomright");
    refreshVideosSearch();
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
      showalert(message, "alert-danger", "formalertdivbottomright");
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
 * Update list of selected videos for modal confirm display
 */
function updateModalConfirmSelectedVideos() {
  let str = "";
  Array.from(getListSelectedVideosTitles()).forEach((title) => {
    str += "<li>" + title + "</li>";
  });
  bulkUpdateConfirmSelectedVideos.innerHTML = str;
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
