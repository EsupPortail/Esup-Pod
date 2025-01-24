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
