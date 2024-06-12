/**
 * @file Esup-Pod script for video access token.
 * @since 3.6.1
 */

const tokenNameForms = document.getElementsByClassName("token-name-form");
for (let tokenNameForm of tokenNameForms) {
  let tokenNameFormInput = tokenNameForm.querySelector(
    ".token-name-form-input",
  );
  let tokenNameFormButton = tokenNameForm.querySelector(
    ".token-name-form-button",
  );
  let initialName = tokenNameFormInput.value;
  tokenNameFormButton.disabled = true;

  tokenNameFormInput.addEventListener("input", function () {
    if (
      tokenNameFormInput.value === initialName ||
      tokenNameFormInput.value === ""
    ) {
      tokenNameFormButton.disabled = true;
    } else {
      tokenNameFormButton.disabled = false;
    }
  });
}

const btnPrivateShare = document.getElementsByClassName("btn-private-share");
for (let i = 0; i < btnPrivateShare.length; i++) {
  let btn = btnPrivateShare[i];
  btn.addEventListener("click", function () {
    var copyText = document.getElementById(btn.dataset.id);
    copyText.select();
    if (!navigator.clipboard) {
      document.execCommand("copy");
    } else {
      navigator.clipboard.writeText(copyText.value);
    }
    showalert(gettext("Text copied"), "alert-info");
  });
}
