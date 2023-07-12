
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

visibilitySelectElement.addEventListener('change', (event) => {
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