/**
 * Hide or show the password field. If it is show, it is required.
 *
 * @param {boolean} toHide For hide the field, set to `true`.
 */
function hidePasswordField(toHide) {
    if (toHide) {
        passwordDivElement.classList.add('d-none');
        passwordInputElement.required = false;
    } else {
        passwordDivElement.classList.remove('d-none');
        passwordInputElement.required = true;
    }
}


/**
 * Update the visibility for the help text.
 *
 * @param {string} visibility The new visibility.
 * @param {HTMLElement} helpText The help text element.
 */
function updateVisibilityHelpText(visibility, helpText) {
    if (visibility == 'public') {
        helpText.innerHTML = gettext('<b>Public:</b> the playlist can be accessed by anyone.');
    } else if (visibility == 'protected') {
        helpText.innerHTML = gettext('<b>Password-protected:</b> the playlist can be accessed by anyone with the appropriate link and password.');
    } else if (visibility == 'private') {
        helpText.innerHTML = gettext('<b>Private:</b> only you have access to this playlist.');
    }
}

const visibilityHelpElement = document.getElementById("id_visibilityHelp");
const visibilityHelpAdvancedElement = document.createElement('small');
visibilityHelpAdvancedElement.id = 'visibilityHelpAdvanced';
visibilityHelpAdvancedElement.classList.add('form-text');
visibilityHelpElement.parentNode.insertBefore(visibilityHelpAdvancedElement, visibilityHelpElement.nextSibling);
visibilityHelpElement.parentNode.insertBefore(document.createElement('br'), visibilityHelpElement.nextSibling);


const visibilitySelectElement = document.getElementById('id_visibility');
const passwordInputElement = document.getElementById('id_password');
const passwordDivElement = passwordInputElement.closest(".list-group-item");

const promotedInputElement = document.getElementById('id_promoted');
const promotedDivElement = promotedInputElement.closest(".list-group-item");

if (visibilitySelectElement.value !== 'protected') {
    hidePasswordField(true);
}
if (visibilitySelectElement.value !== 'public') {
    promotedDivElement.classList.add("d-none");
}
updateVisibilityHelpText(visibilitySelectElement.value, visibilityHelpAdvancedElement)

visibilitySelectElement.addEventListener('change', (event) => {
    updateVisibilityHelpText(event.target.value, visibilityHelpAdvancedElement);
    if (event.target.value == 'protected') {
        hidePasswordField(false);
    } else {
        hidePasswordField(true);
    }

    if (event.target.value == 'public') {
        promotedDivElement.classList.remove("d-none");
    } else {
        promotedDivElement.classList.add("d-none");
    }
})
