/**
 * @file Esup-Pod script for admin panel.
 * @since 3.6.0
 */
const selectedType = document.getElementById("id_type");
const selectedDataType = document.getElementById("id_data_type");
const fieldDataType = document.getElementsByClassName("field-data_type")[0];
const fieldChannel = document.getElementsByClassName("field-Channel")[0];
const fieldTheme = document.getElementsByClassName("field-Theme")[0];
const fieldPlaylist = document.getElementsByClassName("field-Playlist")[0];
const fieldHtml = document.getElementsByClassName("field-html")[0];

/**
 * Function for show field.
 *
 * @param {HTMLElement} field - The field to show.
 */
function showField(field) {
  field.classList.remove("d-none");
  field.classList.add("d-block");
}

/**
 * Function for hide field.
 *
 * @param {HTMLElement} field - The field to hide.
 */
function hideField(field) {
  field.classList.remove("d-block");
  field.classList.add("d-none");
}

/**
 * Function init.
 */
function initializeFieldDisplay() {
  if (selectedType && selectedDataType) {
    if (selectedType.value === "html") {
      showField(fieldHtml);
      hideField(fieldDataType);
    } else {
      hideField(fieldHtml);
      showField(fieldDataType);
    }

    switch (selectedDataType.value) {
      case "channel":
        showField(fieldChannel);
        break;
      case "theme":
        showField(fieldTheme);
        break;
      case "playlist":
        showField(fieldPlaylist);
        break;
      default:
        hideField(fieldChannel);
        hideField(fieldTheme);
        hideField(fieldPlaylist);
        break;
    }
  }
}

/**
 * Listen selectedType and selectedDataType if change.
 */
if (selectedType) {
  selectedType.addEventListener("change", function () {
    handleTypeChange();
    handleDataTypeChange();
  });
}

if (selectedDataType) {
  selectedDataType.addEventListener("change", handleDataTypeChange);
}

/**
 * Function change Type.
 */
function handleTypeChange() {
  if (selectedType && selectedDataType) {
    if (selectedType.value === "html") {
      showField(fieldHtml);
      hideField(fieldDataType);
    } else {
      hideField(fieldHtml);
      showField(fieldDataType);
    }
  }
}

/**
 * Function change Data Type.
 */
function handleDataTypeChange() {
  if (selectedType && selectedDataType) {
    switch (selectedDataType.value) {
      case "channel":
        showField(fieldChannel);
        hideField(fieldTheme);
        hideField(fieldPlaylist);
        break;
      case "theme":
        showField(fieldTheme);
        hideField(fieldChannel);
        hideField(fieldPlaylist);
        break;
      case "playlist":
        showField(fieldPlaylist);
        hideField(fieldChannel);
        hideField(fieldTheme);
        break;
      default:
        hideField(fieldChannel);
        hideField(fieldTheme);
        hideField(fieldPlaylist);
        break;
    }
  }
}

/**
 * Call init function.
 */
initializeFieldDisplay();
