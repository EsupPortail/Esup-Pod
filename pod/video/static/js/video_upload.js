/** Optional upload diagnostics. This file never starts or controls a request. */
(function () {
  "use strict";

  try {
    const form = document.getElementById("uploadForm");
    const status = document.getElementById("upload-status");
    if (!form || !status || typeof window.jQuery !== "function") return;

    const $ = window.jQuery;
    const completePath = new URL(form.dataset.completeUrl, window.location.href).pathname;

    function gettext(message) {
      return typeof window.gettext === "function" ? window.gettext(message) : message;
    }

    function show(message, error = false) {
      status.textContent = message;
      status.classList.toggle("text-danger", error);
    }

    // Event listeners must never throw into jQuery or change an event's outcome.
    function observe(callback) {
      return function () {
        try {
          callback.apply(this, arguments);
        } catch (_) {
          // Diagnostics are optional; leave the existing upload running.
        }
      };
    }

    $(document).on("fileuploadadd.podUploadDiagnostics", "#chunked_upload", observe(function () {
      show("");
    }));
    $(document).on("fileuploadsend.podUploadDiagnostics", "#chunked_upload", observe(function () {
      show(gettext("Uploading…"));
    }));
    $(document).on("fileuploaddone.podUploadDiagnostics", "#chunked_upload", observe(function () {
      show(gettext("Checking your upload…"));
    }));
    $(document).on("fileuploadfail.podUploadDiagnostics", "#chunked_upload", observe(function (event, data) {
      const code = data.jqXHR && data.jqXHR.status;
      if (code === 401 || code === 403) {
        show(gettext("You are no longer authenticated. Please log in again."), true);
      } else {
        show(gettext("An error has occurred. Please try later."), true);
      }
    }));
    $(document).on("ajaxError.podUploadDiagnostics", observe(function (event, xhr, settings) {
      if (new URL(settings.url, window.location.href).pathname === completePath) {
        show(gettext("Unable to confirm the upload. Check your dashboard before uploading the file again."), true);
      }
    }));
    const reset = document.getElementById("resetButton");
    if (reset) reset.addEventListener("click", observe(function () {
      show("");
    }));
  } catch (_) {
    // Loading, initialization or browser support errors cannot block the upload.
  }
})();
