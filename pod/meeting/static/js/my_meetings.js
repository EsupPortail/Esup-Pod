/* Esup-Pod My Meetings JS */

/* exported displayLoader */

var meetingModal = document.getElementById("meetingModal");
meetingModal.addEventListener("show.bs.modal", function (event) {
  // Button that triggered the modal
  const button = event.relatedTarget;
  // Extract info from data-bs-* attributes
  const meetingId = button.getAttribute("data-bs-meeting-id");
  const title = button.getAttribute("data-bs-meeting-title");
  const endUrl = button.getAttribute("data-bs-meeting-end-url");
  const modalHref = button.getAttribute("data-bs-meeting-info-url");
  const isWebinar = button.getAttribute("data-bs-meeting-webinar") == "True";
  const endLiveUrl = button.getAttribute("data-bs-meeting-end-live-url");
  const restartLiveUrl = button.getAttribute(
    "data-bs-meeting-restart-live-url",
  );

  fetch(modalHref, {
    method: "GET",
  })
    .then((response) => {
      if (!response.ok) throw Error(response.statusText);
      return response.json();
    })
    .then(function (data) {
      if (data.msg != "") {
        modalBody.textContent = gettext(
          "Unable to find information about the meeting",
        );
        console.log(data.msg);
      } else {
        // All buttons
        var allLinks = "";
        if (isWebinar) {
          // Buttons for webinar
          const modalRestartLiveLink =
            '<p><a onClick="javascript:displayLoader();" href="' +
            restartLiveUrl +
            '" class="btn btn-primary"><i class="bi bi-broadcast"></i> ' +
            gettext("Restart only the live") +
            "</a></p>";
          const modalEndLiveLink =
            '<p><a onClick="javascript:displayLoader();" href="' +
            endLiveUrl +
            '" class="btn btn-secondary"><i class="bi bi-stop-circle"></i> ' +
            gettext("End only the live") +
            "</a></p>";
          const modalEndLink =
            '<p><a onClick="javascript:displayLoader();" href="' +
            endUrl +
            '" class="btn btn-danger"><i class="bi bi-stop-circle"></i> ' +
            gettext("End the webinar (meeting and live)") +
            "</a></p>";
          allLinks = modalRestartLiveLink + modalEndLiveLink + modalEndLink;
        } else {
          // Buttons for standard meeting
          const modalEndLink =
            '<p><a onClick="javascript:displayLoader();" href="' +
            endUrl +
            '" class="btn btn-danger endlink">' +
            gettext("End the meeting") +
            "</a></p>";
          allLinks = modalEndLink;
        }
        modalBody.innerHTML =
          '<div class="d-flex panel">' +
          '  <div class="item flex-grow-1">' +
          generateHtml(data.info) +
          "  </div>" +
          '  <div class="item">' +
          allLinks +
          "  </div>" +
          "</div>";
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
  modalBody.textContent = meetingId;
  //modalFooterEndLink.setAttribute("href", endUrl)
});

/* TODO: check if level parameter can be removed. */
/**
 * Recursively generate an HTML unordered list version of data
 * @param  {Array}  data  - Data to be displayed
 * @param  {Number} level - level of recursion (useless?)
 * @return {string} Generated HTML
 */
function generateHtml(data, level = 0) {
  let html = "<ul>";
  for (let k in data) {
    if (typeof data[k] === "object") {
      html +=
        "<li><strong>" +
        k +
        ":</strong> " +
        generateHtml(data[k], level++) +
        "</li>";
    } else {
      html += "<li><strong>" + k + ":</strong> " + data[k] + "</li>";
    }
  }
  html += "</ul>";
  return html;
}

var copyButtons = document.querySelectorAll(".pod-btn-copy");
copyButtons.forEach(function (elt) {
  elt.addEventListener("click", function () {
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
  if (navigator.clipboard) {
    navigator.clipboard
      .writeText(value)
      .then(() => {
        showalert(gettext("Text copied."), "alert-info");
      })
      .catch(() => {
        showalert(gettext("Something went wrong."), "alert-danger");
      });
  } else {
    showalert(
      gettext("Functionality accessible only in HTTPS, on a recent browser."),
      "alert-danger",
    );
  }
}

/**
 * Display a loading cursor.
 */
function displayLoader() {
  document.body.style.cursor = "wait";
}
