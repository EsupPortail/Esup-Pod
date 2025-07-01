/**
 * @file Esup-Pod function for handling video duplication confirmation.
 */

/**
 * Displays a confirmation dialog before redirecting the user to a duplication URL.
 *
 * @param {Event} event - The event triggered by clicking the link.
 * @param {string} url - The duplication URL to redirect to if the user confirms.
 * @param {string} confirmationText - The confirmation text to display in the dialog.
 * @returns {boolean} - Returns false if the user cancels the confirmation, otherwise redirects to the URL.
 */
/* exported confirmDuplication */
function confirmDuplication(event, url, confirmationText) {
  if (confirm(confirmationText)) {
    window.location.href = url;
  } else {
    event.preventDefault();
    return false;
  }
}

/**
 * Hides empty dropdown menus and their toggle buttons by adding 'd-none' class.
 * Changes style for favorite button when hide button.
 * Uses Bootstrap's utility classes for visibility control.
 * @returns {void}
 */
function hideEmptyDropdowns() {
  document.querySelectorAll(".dropdown-menu").forEach((menu) => {
    if (menu.children.length === 0) {
      const toggleBtn = menu
        .closest(".card-footer")
        ?.querySelector('[data-bs-toggle="dropdown"]');
      if (toggleBtn) {
        // Hide toggle button and empty menu
        toggleBtn.classList.add("d-none");
        menu.classList.add("d-none");
        // Change style for favorite button
        const favBtn = menu
          .closest(".card-footer")
          ?.querySelector(".favorite-btn-link");
        if (favBtn) {
          favBtn.classList.remove("ms-1");
          favBtn.classList.add("mx-1");
        }
      }
    }
  });
}

document.addEventListener("DOMContentLoaded", function () {
  hideEmptyDropdowns();
});
