const caption_memories = {
  start_time: "00:00.000",
};
const file_prefix = window.location.pathname
  .match(/[\d\w\-]+\/$/)[0]
  .replace("/", "");

document.addEventListener("click", (e) => {
  if (!e.target.parentNode) return;
  if (
    !e.target.parentNode.matches("a.file-name") &&
    !e.target.parentNode.matches("a.file-image")
  )
    return;

  let url = "/podfile/get_file/file/";
  let form = document.getElementById("captionmaker_form");
  let data_form = new FormData(form);

  send_form_data(url, data_form, "ProcessProxyVttResponse");
});

// Charge caption/subtitle file if exists
document.addEventListener("DOMContentLoaded", function () {
  let url_search = new URLSearchParams(window.location.search);
  if (url_search.has("src") && !isNaN(url_search.get("src"))) {
    let url = "/podfile/get_file/file/";
    let data = {
      src: url_search.get("src"),
      csrfmiddlewaretoken: Cookies.get("csrftoken"),
    };

    send_form_data(url, data, "ProcessProxyVttResponse");
  } else {
    document.getElementById(
      "captionFilename",
    ).value = `${file_prefix}_captions_${Date.now()}`;
  }

  let placeholder = gettext(
    "WEBVTT\n\nstart time(00:00.000) --> end time(00:00.000)\ncaption text",
  );
  let captionContent = document.getElementById("captionContent");
  captionContent.setAttribute("placeholder", placeholder);
  captionContent.addEventListener("mouseup", function (e) {
    let selectedText = this.value.substring(
      this.selectionStart,
      this.selectionEnd,
    );

    playSelectedCaption(selectedText.trim());
  });

  captionContent.addEventListener("input propertychange", function () {
    captionsArray.length = 0;
    document.querySelectorAll(".newEditorBlock").forEach((elt) => {
      elt.remove();
    });
    if (this.value.match(/^WEBVTT/)) {
      ParseAndLoadWebVTT(this.value);
    } else {
      alert(gettext("Unrecognized caption file format."));
      t;
    }
  });
});

document.addEventListener("submit", (e) => {
  if (e.target.id != "form_save_captions") return;
  e.preventDefault();
  let caption_content = document.getElementById("captionContent");
  if (!oldModeSelected) caption_content.value = GenerateWEBVTT();

  if (caption_content.value.trim() === "") {
    showalert(gettext("There is no captions to save."), "alert-danger");
    return;
  }
  if (typeof file_loaded != "undefined" && file_loaded) {
    let saveModalId = document.getElementById("saveCaptionsModal");
    let saveModal = bootstrap.Modal.getOrCreateInstance(saveModalId);
    saveModal.show();
  } else {
    document.querySelector('input[name="file_id"]').value = "";
    send_form_save_captions();
  }
});

document.addEventListener("click", (elt) => {
  if (elt.target.id != "modal-btn-new" && elt.target.id != "modal-btn-override")
    return;
  let caption_content = document.getElementById("captionContent");
  if (!oldModeSelected) caption_content.value = GenerateWEBVTT();

  let saveModalId = document.getElementById("saveCaptionsModal");
  let saveModal = bootstrap.Modal.getOrCreateInstance(saveModalId);
  saveModal.hide();

  let form_save_captions = document.getElementById("form_save_captions");
  if (elt.target.id == "modal-btn-override") {
    document
      .getElementById("form_save_captions")
      .querySelector('input[name="file_id"]').value = file_loaded_id;
    //form_save_captions.querySelector('input[name="enrich_ready"]').value = "";
    updateCaptionsArray(caption_content.value);
    send_form_save_captions();
  } else if (elt.target.id == "modal-btn-new") {
    form_save_captions.querySelector('input[name="file_id"]').value = "";
    //form_save_captions.querySelector('input[name="enrich_ready"]').value="";

    send_form_save_captions();
  }
});

const send_form_save_captions = function () {
  let fileName = document.getElementById("captionFilename").value;
  if (fileName.length == 0) {
    fileName = `${file_prefix}_captions_${Date.now()}`;
  }

  rxSignatureLine = /^WEBVTT(?:\s.*)?$/;
  vttContent = document.getElementById("captionContent").value.trim();
  vttLines = vttContent.split(/\r\n|\r|\n/);
  if (!rxSignatureLine.test(vttLines[0])) {
    alert(gettext("Not a valid time track file."));
    return;
  }

  let f = new File([vttContent], fileName + ".vtt", { type: "text/vtt" });
  let data_form = new FormData(document.getElementById("form_save_captions"));

  data_form.append("folder", current_folder);
  data_form.append("file", f);
  url = document.getElementById("form_save_captions").getAttribute("action");

  fetch(url, {
    method: "POST",
    body: data_form,
    headers: {
      "X-Requested-With": "XMLHttpRequest",
    },
    processData: false,
    contentType: false,
  })
    .then((response) => response.text())
    .then((data) => {
      let parser = new DOMParser();
      let htmlDoc = parser.parseFromString(data, "text/html");

      document.body.append(htmlDoc.getElementById("base-message-alert"));
      if (data.track_id != undefined) {
        var url = new URL(window.location.href);
        var url_params = url.searchParams;
        url_params.set("src", data.track_id);
        url.search = url_params.toString();
        location.href = url.toString();
      }
    })

    .catch((error) => {
      showalert(
        gettext("error during exchange") +
          "(" +
          error +
          ")<br>" +
          gettext("no data could be stored."),
        "alert-danger",
      );
    });
};

document
  .getElementById("podvideoplayer")
  .addEventListener("error", function (event) {
    var vh = this.height();

    // error handling straight from the HTML5 video spec (http://dev.w3.org/html5/spec-author-view/video.html)
    if (!event.originalEvent.target.error) return;
    let video_error = document.getElementById("video_error");
    switch (event.originalEvent.target.error.code) {
      case event.originalEvent.target.error.MEDIA_ERR_ABORTED:
        video_error.textContent = gettext("You aborted the video playback.");
        break;
      case event.originalEvent.target.error.MEDIA_ERR_NETWORK:
        video_error.textContent = gettext(
          "A network error caused the video download to fail part-way.",
        );
        break;
      case event.originalEvent.target.error.MEDIA_ERR_DECODE:
        video_error.textContent = gettext(
          "The video playback was aborted due to a corruption problem or because the video used features your browser did not support.",
        );
        break;
      case event.originalEvent.target.error.MEDIA_ERR_SRC_NOT_SUPPORTED:
        video_error.textContent = gettext(
          "The video could not be loaded, either because the server or network failed or because the format is not supported.",
        );

        break;
      default:
        video_error.textContent = gettext("An unknown error occurred.");
        break;
    }
    document.getElementById("videoError").height(vh).style.display = "block";
    this.style.display = "none";
  });

let shortcutsDisplayed = false;
document
  .getElementById("showShortcutTips")
  .addEventListener("click", function (e) {
    let shortcuts = document.getElementById("shortcutsBlock");
    if (shortcutsDisplayed) {
      shortcuts.style.display = "none";
    } else {
      shortcuts.style.display = "block";
    }

    shortcutsDisplayed = !shortcutsDisplayed;
  });

document.getElementById("addSubtitle").addEventListener("click", function (e) {
  const pod = document.getElementById("podvideoplayer");
  const podPlayer = pod.player;
  var playTime = podPlayer.currentTime();
  var captionsEndTime = existingCaptionsEndTime();
  AddCaption(
    captionsEndTime,
    playTime > captionsEndTime ? playTime : parseInt(captionsEndTime) + 2,
    "",
  );
});

document
  .getElementById("clearAllCaptions")
  .addEventListener("click", function (e) {
    e.preventDefault();
    if (confirm(gettext("Are you sure you want to delete all captions?"))) {
      captionsArray.length = 0;
      autoPauseAtTime = -1;

      document.getElementById("captionContent").value = "";
      document.getElementById("captionTitle").innerHTML = "&nbsp;";
      document.getElementById("textCaptionEntry").value = "";
      document.querySelectorAll(".newEditorBlock").forEach((e) => {
        e.remove();
      });
    }
  });

let oldModeSelected = false;

document
  .getElementById("switchOldEditMode")
  .addEventListener("click", function (e) {
    oldModeSelected = !oldModeSelected;

    if (oldModeSelected) {
      document.getElementById("captionContent").value = GenerateWEBVTT();
      document.getElementById("rawCaptionsEditor").style.display = "block";
      document.getElementById("newCaptionsEditor").style.display = "none";
    } else {
      document.getElementById("rawCaptionsEditor").style.display = "none";
      document.getElementById("newCaptionsEditor").style.display = "block";
    }
  });

//  index into captionsArray of the caption being displayed. -1 if none.
var captionBeingDisplayed = -1;

function DisplayExistingCaption(seconds) {
  var ci = FindCaptionIndex(seconds);
  captionBeingDisplayed = ci;
  if (ci != -1) {
    var theCaption = captionsArray[ci];
    let divs = document.querySelectorAll(".vjs-text-track-display div");
    divs[divs.length - 1].innerText = theCaption.caption;
    var message = gettext("Caption for segment from %s to %s:");
    document.getElementById("captionTitle").textContent = interpolate(message, [
      FormatTime(theCaption.start),
      FormatTime(theCaption.end),
    ]);

    document.getElementById("textCaptionEntry").value = theCaption.caption;
    document.getElementById("previewTrack").value = theCaption.caption;
  } else {
    document.getElementById("captionTitle").innerHTML = "&nbsp;";
    document.getElementById("textCaptionEntry").value = "";
    document.getElementById("previewTrack").value = "";
  }
}

function existingCaptionsEndTime() {
  return captionsArray.length > 0
    ? captionsArray[captionsArray.length - 1].end
    : 0;
}

let updateCaptionsArray = (vtt) => {
  let arr = vtt.split("\n\n");
  captionsArray = [];
  document.querySelectorAll(".newEditorBlock").forEach((e) => {
    e.remove();
  });
  arr.forEach((text) => {
    if (text.trim().toLowerCase() !== "webvtt") {
      let data = text.split("\n");
      let times = data[0].split("-->");
      let newCaption = {
        start: ParseTime(times[0]),
        end: ParseTime(times[1]),
        caption: data[1],
      };
      captionsArray.push(newCaption);
      CreateCaptionBlock(newCaption);
    }
  });
};

function videoPlayEventHandler() {
  captionBeingDisplayed = -1;
  //  give Opera a beat before doing this
  window.setTimeout(function () {
    let textCaption = document.getElementById("textCaptionEntry");
    textCaption.value = "";
    textCaption.readOnly = true;
    textCaption.classList.add("playing");
    document.getElementById("pauseButton").disabled = false;
    document
      .querySelectorAll("#playButton, #justSaveCaption, #saveCaptionAndPlay")
      .forEach(function (e) {
        e.disabled = true;
      });
  }, 16);
}

function videoPauseEventHandler() {
  document
    .querySelectorAll("#playButton, #justSaveCaption, #saveCaptionAndPlay")
    .forEach(function (e) {
      e.disabled = false;
    });
  let textCaption = document.getElementById("textCaptionEntry");

  textCaption.classList.remove("playing");
  textCaption.readOnly = false;
  document.getElementById("pauseButton").disabled = false;

  const pod = document.getElementById("podvideoplayer");
  const podPlayer = pod.player;
  var playTime = podPlayer.currentTime();
  var captionsEndTime = existingCaptionsEndTime();
  var message = "";
  if (playTime - 1 < captionsEndTime) {
    var ci = FindCaptionIndex(playTime - 1);
    if (ci != -1) {
      var theCaption = captionsArray[ci];

      message = gettext("Edit caption for segment from %s to %s:");
      document.getElementById("captionTitle").textContent = interpolate(
        message,
        [FormatTime(theCaption.start), FormatTime(theCaption.end)],
      );

      textCaption.value = theCaption.caption;
      captionBeingDisplayed = ci;
    } else {
      document.getElementById("captionTitle").textContent = gettext(
        "No caption at this time code.",
      );
      textCaption.value = "";
      captionBeingDisplayed = -1;
    }
  } else {
    message = gettext("Enter caption for segment from %s to %s:");
    document.getElementById("captionTitle").textContent = interpolate(message, [
      FormatTime(existingCaptionsEndTime()),
      FormatTime(playTime),
    ]);

    document.getElementById("textCaptionEntry").value = "";
    captionBeingDisplayed = -1;
  }

  //$("#textCaptionEntry").focus().get(0).setSelectionRange(1000, 1000); // set focus and selection point to end
}

function videoTimeUpdateEventHandler() {
  const pod = document.getElementById("podvideoplayer");
  const podPlayer = pod.player;
  var playTime = podPlayer.currentTime();
  if (autoPauseAtTime >= 0 && playTime >= autoPauseAtTime) {
    autoPauseAtTime = -1;
    podPlayer.pause();
    return;
  }

  var captionsEndTime = existingCaptionsEndTime();
  if (playTime < captionsEndTime) {
    DisplayExistingCaption(playTime);
  } else {
    var message = gettext("Pause to enter caption for segment from %s to %s.");
    document.getElementById("captionTitle").textContent = interpolate(message, [
      FormatTime(captionsEndTime),
      FormatTime(playTime),
    ]);

    let divs = document.querySelectorAll(".vjs-text-track-display div");
    divs[divs.length - 1].innerText = "";

    if (captionBeingDisplayed != -1) {
      document.getElementById("textCaptionEntry").value = "";
      captionBeingDisplayed = -1;
    }
  }
}

//  this enables the demo after a successful video load
function EnableDemoAfterLoadVideo() {
  document
    .querySelectorAll(".grayNoVideo a, .grayNoVideo")
    .forEach(function (e) {
      e.removeAttribute("style");
    });
  document
    .querySelectorAll(
      ".grayNoVideo a, .grayNoVideo button, .grayNoVideo input, .grayNoVideo textarea",
    )
    .forEach(function (e) {
      e.disabled = false;
    });

  document
    .querySelectorAll("#pauseButton, #saveCaptionAndPlay, #justSaveCaption")
    .forEach(function (e) {
      e.disabled = true;
    });

  document.getElementById("textCaptionEntry").readOnly = true;
}

const pod = document.getElementById("podvideoplayer");

pod.addEventListener("play", videoPlayEventHandler);
pod.addEventListener("timeupdate", videoTimeUpdateEventHandler);
pod.addEventListener("pause", videoPauseEventHandler);
pod.addEventListener("canplay", EnableDemoAfterLoadVideo);
pod.addEventListener("loadeddata", EnableDemoAfterLoadVideo);

document.getElementById("playButton").addEventListener("click", function () {
  const pod = document.getElementById("podvideoplayer");
  const podPlayer = pod.player;
  podPlayer.play();
});

document.getElementById("pauseButton").addEventListener("click", function () {
  const pod = document.getElementById("podvideoplayer");
  const podPlayer = pod.player;
  podPlayer.pause();
});

function GenerateWEBVTT() {
  let vtt = "";
  document
    .querySelectorAll("#newCaptionsEditor > .newEditorBlock")
    .forEach((e) => {
      let captionText = e.querySelector(".captionTextInput").value;
      let startTime = e.querySelector(".startTimeBtn").text;
      let endTime = e.querySelector(".endTimeBtn").text;

      vtt += `\n\n${startTime} --> ${endTime}\n${captionText}`;
    });

  if (vtt.length > 0) vtt = "WEBVTT" + vtt;

  return vtt;
}

function SaveCurrentCaption() {
  const pod = document.getElementById("podvideoplayer");
  const podPlayer = pod.player;
  var playTime = podPlayer.currentTime();
  var captionsEndTime = existingCaptionsEndTime();
  let new_entry = document.getElementById("textCaptionEntry").value;
  if (playTime - 1 < captionsEndTime) {
    var ci = FindCaptionIndex(playTime - 1);
    if (ci != -1) {
      UpdateCaption(ci, new_entry);
    }
  } else {
    AddCaption(captionsEndTime, playTime, new_entry);
  }
}

document
  .getElementById("justSaveCaption")
  .addEventListener("click", function () {
    SaveCurrentCaption();
  });

document
  .getElementById("saveCaptionAndPlay")
  .addEventListener("click", function () {
    SaveCurrentCaption();

    const pod = document.getElementById("podvideoplayer");
    const podPlayer = pod.player;
    podPlayer.play();
  });

document
  .getElementById("textCaptionEntry")
  .addEventListener("keydown", function (e) {
    var code = e.key ?? e.code;
    if (code == "ENTER" && !e.shiftKey) {
      document.getElementById("saveCaptionAndPlay").click();
      return false;
    }
  });

/**
 * Updat caption html content
 */
let updateCaptionHtmlContent = () => {
  let vtt = "WEBVTT\n\n";
  captionsArray.forEach((cap, i) => {
    vtt += `${FormatTime(cap.start)} --> ${FormatTime(cap.end)}\n${
      cap.caption
    }`;
    if (i !== captionsArray.length - 1) vtt += "\n\n";
  });
  document.getElementById("captionContent").value = vtt;
};

function UpdateCaption(ci, captionText) {
  captionsArray[ci].caption = captionText;
  updateCaptionHtmlContent();
}

let lastEditedBlock = null;

function CreateCaptionBlock(newCaption, spawnFunction) {
  let captionText = newCaption.caption;
  let start = FormatTime(newCaption.start);
  let end = FormatTime(newCaption.end);

  let block = {
    // parent
    div: new DOMParser().parseFromString(
      `<div class='newEditorBlock row'></div>`,
      "text/html",
    ).body.firstChild,

    // circle buttons
    buttonsDiv: new DOMParser().parseFromString(
      "<div class='captionButtons col-1 d-flex flex-wrap align-items-center'></div>",
      "text/html",
    ).body.firstChild,

    insertBtn: new DOMParser().parseFromString(
      `<button class="btn btn-light" title="${gettext(
        "Add",
      )}"><i class="bi bi-plus-circle"></i></button>`,
      "text/html",
    ).body.firstChild,
    deleteBtn: new DOMParser().parseFromString(
      `<button class="btn btn-light" title="${gettext(
        "Delete",
      )}"><i class="bi bi-x-circle"></i></button>`,
      "text/html",
    ).body.firstChild,
    // textarea
    captionDiv: new DOMParser().parseFromString(
      "<div class='captionText col'></div>",
      "text/html",
    ).body.firstChild,
    //captionTextInput: $(`<label>${gettext('Caption')}<textarea class='captionTextInput'></textarea></label>`),
    captionTextLabel: new DOMParser().parseFromString(
      `<label>${gettext("Caption")}</label>`,
      "text/html",
    ).body.firstChild,
    captionTextInput: new DOMParser().parseFromString(
      `<textarea class='captionTextInput form-control'></textarea>`,
      "text/html",
    ).body.firstChild,
    // time editable
    timeBlockEditable: new DOMParser().parseFromString(
      `<div class='captionTimestamps col-3' style='display:none'></div>"`,
      "text/html",
    ).body.firstChild,
    startTimeLabel: new DOMParser().parseFromString(
      `<label class="p-2">${gettext("Start")}</label>`,
      "text/html",
    ).body.firstChild,
    startTimeInput: new DOMParser().parseFromString(
      `<input class="form-control" type='text'>`,
      "text/html",
    ).body.firstChild,
    endTimeLabel: new DOMParser().parseFromString(
      `<label class="p-2">${gettext("End")}</label>`,
      "text/html",
    ).body.firstChild,
    endTimeInput: new DOMParser().parseFromString(
      `<input class="form-control" type='text'>`,
      "text/html",
    ).body.firstChild,

    // time links
    timeBlock: new DOMParser().parseFromString(
      `<div class='captionTimestamps col-sm-3 col-md-2'><span>${gettext(
        "Time stamps",
      )}</span></div>`,
      "text/html",
    ).body.firstChild,
    startTimeBtn: new DOMParser().parseFromString(
      `<a class='startTimeBtn btn-link' href='#podvideoplayer'>${start}</a>`,
      "text/html",
    ).body.firstChild,
    endTimeBtn: new DOMParser().parseFromString(
      `<a class='endTimeBtn btn-link' href='#podvideoplayer'>${end}</a>`,
      "text/html",
    ).body.firstChild,
    // flags
    isEditEnabled: false,

    // methods
    enableEdit: function () {
      if (!this.isEditEnabled) {
        if (lastEditedBlock) {
          lastEditedBlock.disableEdit();
        }

        this.startTimeInput.value = this.startTimeBtn.textContent;

        this.endTimeInput.value = this.endTimeBtn.textContent;

        this.timeBlockEditable.style.display = "";
        this.timeBlock.style.display = "none";
        this.div.classList.add("captionBeingEdited");

        lastEditedBlock = this;

        this.isEditEnabled = true;
      }
    },

    disableEdit: function () {
      if (this.isEditEnabled) {
        let newStartTime = ParseTime(this.startTimeInput.value);
        let newEndTime = ParseTime(this.endTimeInput.value);

        newCaption.start = newStartTime;
        newCaption.end = newEndTime;

        this.startTimeBtn.textContent = FormatTime(newStartTime);
        this.endTimeBtn.textContent = FormatTime(newEndTime);

        this.timeBlockEditable.style.display = "none";
        this.timeBlock.style.display = "";
        this.div.classList.remove("captionBeingEdited");

        this.placeInOrder();
        this.isEditEnabled = false;
      }
    },

    placeInOrder: function () {
      for (let i in captionsArray) {
        let cap = captionsArray[i];
        if (cap.start > newCaption.start) {
          // move caption object in captionsArray
          let index = Array.from(this.div.parentNode.children).indexOf(
            this.div,
          );
          let fromI = index;
          let toI = fromI < i ? i - 1 : i;
          captionsArray.splice(fromI, 1);
          captionsArray.splice(toI, 0, newCaption);

          // move the element in DOM
          this.div.remove();
          cap.blockObject.div.parentNode.insertBefore(
            this.div,
            cap.blockObject.div,
          );
          return;
        }
      }

      // if this caption is the last, move it to the end
      if (this.div.parenNode) {
        let index = Array.from(this.div.parentNode.children).indexOf(this.div);
        captionsArray.splice(index, 1);
        captionsArray.push(newCaption);
        let addSubtitle = document.getElementById("addSubtitle");
        addSubtitle.parentNode.insertBefore(this.div, addSubtitle);
      }
    },

    spawnNew: function () {
      const pod = document.getElementById("podvideoplayer");
      const podPlayer = pod.player;
      let playTime = podPlayer.currentTime();
      let captionObj = {
        start: newCaption.end,
        end:
          playTime > newCaption.end ? playTime : parseInt(newCaption.end) + 2,
        caption: "",
      };
      let index = Array.from(this.div.parentNode.children).indexOf(this.div);

      captionsArray.splice(index + 1, 0, captionObj);
      CreateCaptionBlock(captionObj, (newDiv) =>
        this.div.parentNode.insertBefore(newDiv, this.div.nextSibling),
      );
    },

    delete: function () {
      let index = Array.from(this.div.parentNode.children).indexOf(this.div);

      captionsArray.splice(index, 1);
      this.div.remove();
    },

    init: function () {
      var uniq = "c" + Math.floor(Math.random() * 100000000);
      this.div.captionBlockObject = this;

      this.captionTextInput.value = captionText;

      this.captionTextInput.setAttribute("id", uniq);
      this.captionTextLabel.setAttribute("for", uniq);

      this.insertBtn.addEventListener("click", () => this.spawnNew());
      this.deleteBtn.addEventListener("click", () => this.delete());
      this.startTimeBtn.addEventListener("click", () =>
        seekVideoTo(newCaption.start),
      );
      this.endTimeBtn.addEventListener("click", () =>
        seekVideoTo(newCaption.end),
      );
      this.captionTextInput.addEventListener("focus", () => this.enableEdit());

      this.timeBlock.append(this.startTimeBtn);
      this.timeBlock.append(this.endTimeBtn);
      this.startTimeInput.setAttribute("id", "start_" + uniq);
      this.startTimeLabel.setAttribute("for", "start_" + uniq);
      this.endTimeInput.setAttribute("id", "end_" + uniq);
      this.endTimeLabel.setAttribute("for", "end_" + uniq);
      this.timeBlockEditable.append(
        this.startTimeLabel,
        this.startTimeInput,
        this.endTimeLabel,
        this.endTimeInput,
      );
      this.buttonsDiv.append(this.insertBtn, this.deleteBtn);

      this.captionDiv.append(this.captionTextLabel, this.captionTextInput);

      this.div.append(
        this.buttonsDiv,
        this.captionDiv,
        this.timeBlock,
        this.timeBlockEditable,
      );

      this.startTimeInput.addEventListener("keydown", (e) => {
        if (e.key == "ENTER") this.disableEdit();
      });

      this.endTimeInput.addEventListener("keydown", (e) => {
        if (e.key == "ENTER") this.disableEdit();
      });

      document.addEventListener("click", (e) => {
        var target = e.target;
        let selector = "";
        this.div.classList.forEach((className) => {
          selector += " ." + className;
        });

        // some weird bug where the
        if (target.querySelectorAll(selector).length) this.disableEdit();
      });
    },
  };

  block.init();
  newCaption.blockObject = block;

  if (spawnFunction) {
    spawnFunction(block.div);
  } else {
    let addSubtitle = document.getElementById("addSubtitle");
    addSubtitle.parentNode.insertBefore(block.div, addSubtitle);
  }

  block.captionTextInput.addEventListener("input propertychange", function () {
    captionsArray[block.div.index()].caption = this.value;
  });

  block.div.addEventListener(
    "hover",
    function () {
      highlightVideoRegion(newCaption.start, newCaption.end);
    },
    function () {
      clearVideoRegion();
    },
  );
  document.getElementById("noCaptionsText")?.remove();

  return block;
}

let editorShortcuts = {
  Delete: function (e) {
    if (e.altKey && lastEditedBlock) {
      lastEditedBlock.delete();
      return false;
    }
  },
  PageUp: function (e) {
    if (lastEditedBlock) {
      let prev = lastEditedBlock.div.previousElementSibling;
      if (prev) {
        let textarea = prev.querySelector("textarea");
        textarea.focus();
        return false;
      }
    }
  },
  PageDown: function (e) {
    if (lastEditedBlock) {
      let next = lastEditedBlock.div.nextElementSibling;
      if (next) {
        let textarea = next.querySelector("textarea");
        textarea.focus();
        return false;
      }
    }
  },
  ArrowLeft: function (e) {
    if (this.notFocused()) {
      seekVideo(-10);
      return false;
    }
  },
  ArrowRight: function (e) {
    if (this.notFocused()) {
      seekVideo(10);
      return false;
    }
  },
  " ": function (e) {
    // space
    if (this.notFocused()) {
      const pod = document.getElementById("podvideoplayer");
      const podPlayer = pod.player;
      let player = podPlayer;
      if (player.paused()) player.play();
      else player.pause();

      return false;
    }
  },
  m: function (e) {
    if (this.notFocused()) {
      let player = podPlayer;

      const pod = document.getElementById("podvideoplayer");
      const podPlayer = pod.player;
      player.muted(!player.muted());
      return false;
    }
  },
  "?": function (e) {
    if (this.notFocused()) {
      document.getElementById("showShortcutTips").click();
      return false;
    }
  },
  Insert: function (e) {
    if (lastEditedBlock) {
      lastEditedBlock.spawnNew();
    } else {
      document.getElementById("addSubtitle").click();
    }

    return false;
  },
  s: function (e) {
    if (e.ctrlKey) {
      document.getElementById("justSaveCaption").click();
      return false;
    }
  },
  End: function (e) {
    document.getElementById("saveCaptionAndPlay").click();
    return false;
  },

  notFocused: function () {
    var focused = document.activeElement;
    return focused.length == 0;
  },

  init: function () {
    let self = this;
    document.addEventListener("keydown", function (e) {
      if (self[e.key]) {
        return self[e.key](e);
      }
    });
  },
};

editorShortcuts.init();

function AddCaptionListRow(ci, newCaption) {
  let vtt = document.getElementById("captionContent");
  let vtt_entry = document.getElementById("textCaptionEntry").value.trim();
  let start = caption_memories.start_time;

  const pod = document.getElementById("podvideoplayer");
  const podPlayer = pod.player;
  var end = FormatTime(podPlayer.currentTime());
  var captionsEndTime = existingCaptionsEndTime();
  let caption_text = `${start} --> ${end}\n${vtt_entry}`;
  if (vtt_entry !== "") {
    if (vtt.value.trim() === "") {
      vtt.value = `WEBVTT\n\n${caption_text}`;
    } else {
      vtt.value = `${vtt.value}\n\n${caption_text}`;
    }
  }

  CreateCaptionBlock(newCaption);
  caption_memories.start_time = end;
}

function AddCaption(captionStart, captionEnd, captionText) {
  const pod = document.getElementById("podvideoplayer");
  const podPlayer = pod.player;
  let videoDuration = podPlayer.duration();
  captionStart = Math.max(Math.min(captionStart, videoDuration), 0);
  captionEnd = Math.max(Math.min(captionEnd, videoDuration), 0);

  let newCaption = {
    start: captionStart,
    end: captionEnd,
    caption: captionText.trim(),
  };

  captionsArray.push(newCaption);
  AddCaptionListRow(captionsArray.length - 1, newCaption);
}

function hmsToSecondsOnly(str) {
  let p = str.split(":"),
    s = 0,
    m = 1;
  while (p.length > 0) {
    s += m * (parseInt(p.pop(), 10) || 0);
    m *= 60;
  }
  return s;
}

// parses webvtt time string format into floating point seconds
function ParseTime(sTime) {
  let seconds = hmsToSecondsOnly(sTime);
  return parseFloat(seconds + "." + (sTime.split(".")[1] || 0));
  /*//  parse time formatted as hours:mm:ss.sss where hours are optional
    if (sTime) {
        if (m != null) {
            return (m[1] ? parseFloat(m[1]) : 0) * 3600 + parseFloat(m[2]) * 60 + parseFloat(m[3]);
        } else {
            m = sTime.match(/^\s*(\d{2}):(\d{2}):(\d{2}):(\d{2})\s*$/);
            if (m != null) {
                var seconds = parseFloat(m[1]) * 3600 + parseFloat(m[2]) * 60 + parseFloat(m[3]) + parseFloat(m[4]) / 30;
                return seconds;
            }
        }
    }
    return 0;*/
}

// formats floating point seconds into the webvtt time string format
function FormatTime(seconds) {
  var hh = Math.floor(seconds / (60 * 60));
  var mm = Math.floor(seconds / 60) % 60;
  var ss = seconds % 60;
  return (
    (hh == 0 ? "" : (hh < 10 ? "0" : "") + hh.toString() + ":") +
    (mm < 10 ? "0" : "") +
    mm.toString() +
    ":" +
    (ss < 10 ? "0" : "") +
    ss.toFixed(3)
  );
}

function FindCaptionIndex(seconds) {
  var below = -1;
  var above = captionsArray.length;
  var i = Math.floor((below + above) / 2);
  while (below < i && i < above) {
    if (captionsArray[i].start <= seconds && seconds < captionsArray[i].end)
      return i;

    if (seconds < captionsArray[i].start) {
      above = i;
    } else {
      below = i;
    }
    i = Math.floor((below + above) / 2);
  }
  return -1;
}

function playSelectedCaption(timeline) {
  if (timeline.includes("-->")) {
    let times = timeline.trim().split(/\s?\-\->\s?/);
    let start = times[0].match(/[\d:\.]/) ? ParseTime(times[0]) : null;
    let end = times[1].match(/[\d:\.]/) ? ParseTime(times[1]) : null;
    if (!isNaN(start) && !isNaN(end)) {
      const pod = document.getElementById("podvideoplayer");
      const podPlayer = pod.player;
      var vid = podPlayer;
      vid.currentTime(start);
      autoPauseAtTime = end;
      vid.play();
    }
  }
}

/**
 * Escape Html entities
 */
function XMLEncode(s) {
  return s
    .replace(/\&/g, "&amp;")
    .replace(/“/g, "&quot;")
    .replace(/”/g, "&quot;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function XMLDecode(s) {
  return s
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&apos;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&amp;/g, "&");
}

function LoadCaptionFile(fileObject) {
  if (window.FileReader) {
    var reader = new window.FileReader();

    reader.addEventListener("load", function () {
      ProcessProxyVttResponse({ status: "success", response: reader.result });
    });

    reader.addEventListener("onerror", function (evt) {
      alert(gettext("Error reading caption file. Code = ") + evt.code);
    });

    try {
      reader.readAsText(fileObject);
    } catch (exc) {
      alert(
        gettext("Exception thrown reading caption file. Code = ") + exc.code,
      );
    }
  } else {
    alert(gettext("Your browser does not support FileReader."));
  }
}

// invoked by script insertion of proxyvtt.ashx
function ProcessProxyVttResponse(obj) {
  obj = JSON.parse(obj);
  if (obj.status == "error")
    alert(gettext("Error loading caption file: ") + obj.message);
  else if (obj.status == "success") {
    //  delete any captions we've got
    captionsArray.length = 0;
    file_loaded = true;
    file_loaded_id = obj.id_file;
    current_folder = obj.id_folder;
    document.querySelectorAll(".newEditorBlock").forEach((elt) => {
      elt.remove();
    });

    // strip file extension and set as title
    document.getElementById("captionFilename").value = obj.file_name.replace(
      /\.[^/.]+$/,
      "",
    );

    if (obj.response.match(/^WEBVTT/)) {
      ParseAndLoadWebVTT(obj.response);
    } else {
      alert(gettext("Unrecognized caption file format."));
    }
  }
}

//-----------------------------------------------------------------------------------------------------------------------------------------
//  Partial parser for WebVTT files based on the spec at http://dev.w3.org/html5/webvtt/
//-----------------------------------------------------------------------------------------------------------------------------------------

function ParseAndLoadWebVTT(vtt) {
  var vttLines = vtt.split(/\r\n|\r|\n/); // create an array of lines from our file

  if (vttLines[0].trim().toLowerCase() != "webvtt") {
    // must start with a signature line
    alert(gettext("Not a valid time track file."));
    return;
  }

  document.querySelectorAll(".newEditorBlock").forEach((elt) => {
    elt.remove();
  });

  var rxTimeLine = /^([\d\.:]+)\s+-->\s+([\d\.:]+)(?:\s.*)?$/;
  var rxCaptionLine = /^(?:<v\s+([^>]+)>)?([^\r\n]+)$/;
  var rxBlankLine = /^\s*$/;
  var rxMarkup = /<[^>]>/g;

  var cueStart = null,
    cueEnd = null,
    cueText = null;

  function appendCurrentCaption() {
    if (cueStart && cueEnd && cueText) {
      let newCaption = {
        start: cueStart,
        end: cueEnd,
        caption: cueText.trim(),
      };
      captionsArray.push(newCaption);
      CreateCaptionBlock(newCaption);
    }
    cueStart = cueEnd = cueText = null;
  }

  for (var i = 1; i < vttLines.length; i++) {
    if (rxBlankLine.test(vttLines[i])) {
      appendCurrentCaption();
      continue;
    }

    if (!cueStart && !cueEnd && !cueText && vttLines[i].indexOf("-->") == -1) {
      //  this is a cue identifier we're ignoring
      continue;
    }

    var timeMatch = rxTimeLine.exec(vttLines[i]);
    if (timeMatch) {
      appendCurrentCaption();
      cueStart = ParseTime(timeMatch[1]);
      if (cueStart == 0) cueStart = "0.0";
      cueEnd = ParseTime(timeMatch[2]);
      continue;
    }

    var captionMatch = rxCaptionLine.exec(vttLines[i]);
    if (captionMatch && cueStart && cueEnd) {
      //  captionMatch[1] is the optional voice (speaker) we're ignoring
      var capLine = captionMatch[2].replace(rxMarkup, "");
      if (cueText) cueText += " " + capLine;
      else {
        cueText = capLine;
      }
    }
  }
  appendCurrentCaption();
  document.getElementById("captionContent").value = vtt;
}

// videojs region highlighting

var highlightVideoRegion;
var clearVideoRegion;

const registerPlugin = videojs.registerPlugin || videojs.plugin;

const onPlayerReady = function (player, options) {
  let startKeyframe;
  let endKeyframe;
  let regionHighlight;

  const clearVideoRegion = () => {
    startKeyframe?.remove();

    endKeyframe?.remove();

    regionHighlight?.remove();

    player.userActive(false);
  };

  highlightVideoRegion = function (startTime, endTime) {
    clearVideoRegion();
    player.userActive(true);

    let startPercent = (startTime / player.duration()) * 100;
    let endPercent = (endTime / player.duration()) * 100;

    startPercent = Math.max(Math.min(startPercent, 100), 0);
    endPercent = Math.max(Math.min(endPercent, 100), 0);

    startKeyframe = `<svg class='keyframe keyframe-left' xmlns="http://www.w3.org/2000/svg" width="6" height="11" viewBox="0 0 6 11">
        <path id="Path_4" data-name="Path 4" d="M4.667,0H1.333A1.281,1.281,0,0,0,0,1.222V6.256L6,11V1.222A1.281,1.281,0,0,0,4.667,0Z" fill="#ad327a"/>
      </svg>`;
    startKeyframe.style = "left: " + `${startPercent}%`;

    let element = player.controlBar.progressControl.seekBar.playProgressBar.el_;
    element.parentNode.insertBefore(startKeyframe, element);

    regionHighlight = "<div class='regionHighligh'></div>";
    regionHighlight.style = "left: " + `${startPercent}%`;
    regionHighlight.style = "width:" + `${endPercent - startPercent}%`;

    startKeyframe.after(regionHighlight);

    endKeyframe = `<svg class='keyframe keyframe-right' xmlns="http://www.w3.org/2000/svg" width="6" height="11" viewBox="0 0 6 11">
        <path id="Path_5" data-name="Path 5" d="M1.333,0H4.667A1.281,1.281,0,0,1,6,1.222V6.256L0,11V1.222A1.281,1.281,0,0,1,1.333,0Z" fill="#ad327a"/>
      </svg>`;
    endKeyframe.style = "left" + `${endPercent}%`;
    regionHighlight.after(endKeyframe);
  };

  seekVideoTo = function (time) {
    player.userActive(true);
    player.currentTime(time);
  };

  seekVideo = function (time) {
    player.userActive(true);
    player.currentTime(player.currentTime() + time);
  };
};

const timelineRegions = function (options) {
  this.ready(function () {
    onPlayerReady(this, options);
  });
};

registerPlugin("timelineRegions", timelineRegions);

videojs.hook("setup", function (player) {
  player.timelineRegions();
});
