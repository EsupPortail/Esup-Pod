
/**
 * Hide or show the password field. If it is show, it is required.
 *
 * @param {boolean} toHide For hide the field, set to `true`.
 */
function hidePasswordField(toHide) {
    if (toHide) {
        passwordDivElement.style.display = 'none';
        passwordInputElement.required = false;
    } else {
        passwordDivElement.style.display = 'block';
        passwordInputElement.required = true;
    }
}

const passwordInputElement = document.getElementById('id_password');
const passwordDivElement = passwordInputElement.parentElement.parentElement;
const visibilitySelectElement = document.getElementById('id_visibility');
hidePasswordField(true);
visibilitySelectElement.addEventListener('change', (event) => {
    if (event.target.value == 'protected') {
        hidePasswordField(false);
    } else {
        hidePasswordField(true);
    }
})