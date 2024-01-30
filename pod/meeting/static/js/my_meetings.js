/* Esup-Pod My Meetings JS */

var meetingModal = document.getElementById("meetingModal");
meetingModal.addEventListener("show.bs.modal", function (event) {
  // Button that triggered the modal
  const button = event.relatedTarget;
  // Extract info from data-bs-* attributes
  const meeting_id = button.getAttribute("data-bs-meeting-id");
  const title = button.getAttribute("data-bs-meeting-title");
  const endurl = button.getAttribute("data-bs-meeting-end-url");
  const modalHref = button.getAttribute("data-bs-meeting-info-url");

  fetch(modalHref, {
    method: "GET",
  })
    .then((response) => {
      if (!response.ok) throw Error(response.statusText);
      return response.json();
    })
    .then(function (data) {
      if (data.msg != "") {
        modalBody.innerHTML = gettext(
          "Unable to find information about the meeting",
        );
        console.log(msg);
      } else {
        const modalendlink =
          '<p><a href="' +
          endurl +
          '" class="btn btn-danger endlink">' +
          gettext("End the meeting") +
          "</a></p>";
        modalBody.innerHTML = generateHtml(data.info) + modalendlink;
      }
    })
    .catch((error) => {
      console.error(error);
    });

  //
  // Update the modal's content.
  const modalTitle = meetingModal.querySelector(".modal-title");
  const modalBody = meetingModal.querySelector(".modal-body");
  //const modalFooterEndLink = meetingModal.querySelector('.modal-footer a.endlink')

  modalTitle.textContent = title;
  modalBody.textContent = meeting_id;
  //modalFooterEndLink.setAttribute("href", endurl)
});

/* TODO: check if level parameter can be removed. */
/**
 * Recursively generate an HTML unordered list version of data
 * @param  {Array} data   Data to be displayed
 * @param  {Number} level level of recursion (useless?)
 * @return {string}       Generated HTML
 */
function generateHtml(data, level = 0) {
  html = "<ul>";
  for (let k in data) {
    if (typeof data[k] === "object") {
      html +=
        "<li><b>" + k + ":</b> " + generateHtml(data[k], level++) + "</li>";
    } else {
      html += "<li><b>" + k + ":</b> " + data[k] + "</li>";
    }
  }
  html += "</ul>";
  return html;
}

var copyButtons = document.querySelectorAll(".pod-btn-copy");
copyButtons.forEach(function (elt) {
  elt.addEventListener("click", function (event) {
    const input_id = this.dataset.copyvalue;
    copyValue(input_id);
  });
});

/**
 * Copy a value in client clipboard, then display a feedback.
 * @param  {String} value The value to be copied
 * @return {void}
 */
function copyValue(value) {
  navigator.clipboard
    .writeText(value)
    .then(() => {
      showalert(gettext("Text copied."), "alert-success");
    })
    .catch(() => {
      showalert(gettext("Something went wrong."), "alert-danger");
    });
}
