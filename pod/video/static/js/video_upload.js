/** Esup-Pod optional upload diagnostics. This file never starts or controls a request. */
(function () {
  "use strict";

  try {
    const form = document.getElementById("uploadForm");
    const status = document.getElementById("upload-status");
    if (!form || !status) return;

    function gettext(message) {
      return typeof window.gettext === "function"
        ? window.gettext(message)
        : message;
    }

    function show(message, error = false) {
      status.textContent = message;
      status.classList.toggle("text-danger", error);
    }

    // Event listeners must never interrupt the upload or change an event's outcome.
    function observe(callback) {
      return function () {
        try {
          callback.apply(this, arguments);
        } catch (_) {
          // Diagnostics are optional; leave the existing upload running.
        }
      };
    }

    form.addEventListener(
      "pod-upload-status",
      observe(function (event) {
        const { phase, status: code } = event.detail;
        switch (phase) {
          case "fileuploadadd":
            show("");
            break;
          case "fileuploadsend":
            show(gettext("Uploading…"));
            break;
          case "fileuploaddone":
            show(gettext("Checking your upload…"));
            break;
          case "fileuploadfail":
            if (code === 401 || code === 403) {
              show(
                gettext(
                  "You are no longer authenticated. Please log in again.",
                ),
                true,
              );
            } else {
              show(gettext("An error has occurred. Please try later."), true);
            }
            break;
          case "complete-error":
            show(
              gettext(
                "Unable to confirm the upload. Check your dashboard before uploading the file again.",
              ),
              true,
            );
            break;
        }
      }),
    );
    const reset = document.getElementById("resetButton");
    if (reset)
      reset.addEventListener(
        "click",
        observe(function () {
          show("");
        }),
      );
  } catch (_) {
    // Loading, initialization or browser support errors cannot block the upload.
  }
})();
