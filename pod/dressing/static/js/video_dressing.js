/**
 * @file Esup-Pod functions for the dressing form.
 * @since 3.5.0
 */

/**
 * Get the opacity and position fields
 */
let opacityField = document.getElementById("id_opacity");
let positionField = document.getElementById("id_position");
let watermarkField = document.getElementById("id_watermark");

/**
 * Manage field state when modifying watermark field
 */
function handleWatermarkChange() {
  if (watermarkField.value !== "") {
    opacityField.disabled = false;
    positionField.disabled = false;
  } else {
    opacityField.disabled = true;
    positionField.disabled = true;
  }
}

/**
 * Disable opacity and position fields on page load
 */
handleWatermarkChange();

/**
 * Create a mutation observer
 */
var observer = new MutationObserver(function (mutations) {
  mutations.forEach(function (mutation) {
    if (mutation.attributeName === "value") {
      handleWatermarkChange();
    }
  });
});

/**
 * Observe the mutations of the "value" attribute of the watermark field
 */
observer.observe(watermarkField, { attributes: true });

/**
 * Deselect all radio input buttons
 */
function resetRadioButtons() {
  const radioButtons = document.querySelectorAll(
    '#apply_dressing input[type="radio"]',
  );
  radioButtons.forEach((button) => {
    button.checked = false;
  });
}
