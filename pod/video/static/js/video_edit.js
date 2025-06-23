/**
 *  Javascript for Esup-Portal video_edit form
 **/

// Read-only globals defined in main.js
/* global channel_callback init_theme_selector */

// Read-only globals defined in video_edit.html
/* global listTheme */

document.addEventListener(
  "DOMContentLoaded",
  function () {
    const visibilitySelect = document.getElementById("id_visibility");
    const passwordField = document.getElementById("id_password").parentElement;
    visibilitySelect.addEventListener("change", () =>
      toggleFields(visibilitySelect, passwordField),
    );
    toggleFields(visibilitySelect, passwordField);
    // Display type description as field help when changed
    const target = "id_type";
    // Cannot be used in django admin pages, as <div class="help"> has no id.
    const helpContainer = document.getElementById(target + "Help");
    const selector = document.getElementById(target);
    display_option_desc(selector, helpContainer);
    selector.addEventListener("change", function () {
      display_option_desc(this, helpContainer);
    });
  },
  false,
);

/**
 * Apply the select2 style to the select elements.
 */
function applySelect2Style() {
  const select2Containers = document.querySelectorAll(".select2-container");
  console.log(select2Containers);
  select2Containers.forEach((container) => {
    container.style.width = "100%";
  });
}

/**
 * Toggle the password field visibility based on the visibility select value.
 *
 * @param {HTMLSelectElement} visibilitySelect - The select element with the visibility options.
 * @param {HTMLElement} passwordField - The password field container.
 */
function toggleFields(visibilitySelect, passwordField) {
  const idRestrictToGroupsField = document.getElementById(
    "id_restrict_access_to_groups",
  );
  const idIsRestrictedField = document.getElementById("id_is_restricted");
  if (visibilitySelect.value === "restricted") {
    passwordField.closest(".field-password").classList.add("show");
    if (idIsRestrictedField) {
      // For first call, apply select2 style to the select elements.
      if (idIsRestrictedField.checked) {
        applySelect2Style();
        idRestrictToGroupsField
          .closest(".field-restrict_access_to_groups")
          .classList.add("show");
      }
      // ---
      idIsRestrictedField.addEventListener("change", () => {
        if (idIsRestrictedField.checked) {
          applySelect2Style();
          idRestrictToGroupsField
            .closest(".field-restrict_access_to_groups")
            .classList.add("show");
        } else {
          idRestrictToGroupsField
            .closest(".field-restrict_access_to_groups")
            .classList.remove("show");
        }
      });
      idIsRestrictedField.closest(".field-is_restricted").classList.add("show");
    }
  } else {
    passwordField.closest(".field-password").classList.remove("show");
    if (idRestrictToGroupsField) {
      document
        .querySelectorAll("#id_restrict_access_to_groups select")
        .forEach((select) => {
          select.options.forEach((option) => {
            if (option.selected) {
              option.selected = false;
            }
          });
        });
      if (idRestrictToGroupsField) {
        idRestrictToGroupsField
          .closest(".field-restrict_access_to_groups")
          .classList.remove("show");
      }
      if (idIsRestrictedField) {
        idIsRestrictedField
          .closest(".field-is_restricted")
          .classList.remove("show");
      }
    }
  }
}

/**
 * Display the description of the selected option in a select box.
 *
 * @param {HTMLElement} selectBox - The select element.
 * @param {HTMLElement} container - The container element where the description will be displayed.
 */
function display_option_desc(selectBox, container) {
  // Display in $container the title of current $selectedBox option.
  var target_title =
    selectBox.options[selectBox.selectedIndex].getAttribute("title");
  if (!target_title) {
    target_title = gettext("Select the general type of the video.");
  }
  container.textContent = target_title;
}

// Test if we are on video Edit form
if (document.getElementById("video_form")) {
  /** Channel **/
  let id_channel = document.getElementById("id_channel");
  if (id_channel) {
    const id_theme = document.getElementById("id_theme");

    // Callback function to execute when mutations are observed
    const id_channel_callback = (mutationList, observer) => {
      for (const mutation of mutationList) {
        if (mutation.type === "childList") {
          channel_callback(id_channel, id_theme, listTheme);
        }
      }
    };
    // Create an observer instance linked to the callback function
    const id_channel_config = {
      attributes: false,
      childList: true,
      subtree: false,
    };
    const id_channel_observer = new MutationObserver(id_channel_callback);
    var select_channel_observer = new MutationObserver(function (mutations) {
      if (
        id_channel.parentElement.querySelector(".select2-selection__rendered")
      ) {
        id_channel_observer.observe(
          id_channel.parentElement.querySelector(
            ".select2-selection__rendered",
          ),
          id_channel_config,
        );
        select_channel_observer.disconnect();
      }
    });
    select_channel_observer.observe(id_channel.parentElement, {
      //document.body is node target to observe
      childList: true, // This is a must have for the observer with subtree
      subtree: true, // Set to true if changes must also be observed in descendants.
    });

    init_theme_selector(id_channel, id_theme, listTheme);
  }
}
/** end channel **/

// Change notification setting text to stick with a video upload context
const notificationMessage = document.querySelector(
  "#notification-toast>.toast-body>p",
);
if (notificationMessage) {
  notificationMessage.textContent = gettext(
    "Get notified when the video encoding is finished.",
  );
}

// Scheduling logic
var schedulingCheckbox = document.getElementById("id_enable_scheduling");
var dateGroup = document.getElementById("scheduled_publish_date_group");
var dateInput = document.getElementById("id_scheduled_publish_date");
if (schedulingCheckbox && dateGroup && dateInput) {
  function toggleScheduledDate() {
    if (schedulingCheckbox.checked) {
      dateGroup.style.display = "block";
      dateInput.style.display = ""; 
    } else {
      dateGroup.style.display = "none";
      dateInput.style.display = "none";
      dateInput.value = "";
    }
  }
  schedulingCheckbox.addEventListener("change", toggleScheduledDate);
  // Initial state
  toggleScheduledDate();
}
