const caption_memories = {
  start_time: "00:00.000",
};
const file_prefix = window.location.pathname
  .match(/[\d\w\-]+\/$/)[0]
  .replace("/", "");

$(document).on("click", "a.file-name, a.file-image", function () {
  let url = "/podfile/get_file/file/";
  let data_form = $("#captionmaker_form").serializeArray();
  send_form_data(url, data_form, "ProcessProxyVttResponse");
});

// Charge caption/subtitle file if exists
$(document).ready(function () {
  let url_search = new URLSearchParams(window.location.search);
  if (url_search.has("src") && !isNaN(url_search.get("src"))) {
    let url = "/podfile/get_file/file/";
    let data = {
      src: url_search.get("src"),
      csrfmiddlewaretoken: Cookies.get("csrftoken"),
    };
    send_form_data(url, data, "ProcessProxyVttResponse");
  }
  else {
    $("#captionFilename").val(`${file_prefix}_captions_${Date.now()}`);
  }
  
  let placeholder = gettext(
    "WEBVTT\n\nstart time(00:00.000) --> end time(00:00.000)\ncaption text"
  );
  let captionContent = $("#captionContent");
  captionContent.attr("placeholder", placeholder);
  captionContent.on("mouseup", function (e) {
    let selectedText = $(this)
      .val()
      .substring(this.selectionStart, this.selectionEnd);
    playSelectedCaption(selectedText.trim());
  });
  
  captionContent.bind('input propertychange', function () {
    captionsArray.length = 0;
    if (this.value.match(/^WEBVTT/)) {
      ParseAndLoadWebVTT(this.value);
    } else {
      alert(gettext("Unrecognized caption file format."));
    }
  });
});

$(document).on("submit", "#form_save_captions", function (e) {
  e.preventDefault();

  if (!oldModeSelected)
    $("#captionContent").val(GenerateWEBVTT());

  if ($("#captionContent").val().trim() === "") {
    showalert(gettext("There is no captions to save"), "alert-danger");
    return;
  }
  if (typeof file_loaded != "undefined" && file_loaded) {
    $("#saveCaptionsModal").modal("show");
  } else {
    $(this).find('input[name="file_id"]').val("");
    send_form_save_captions();
  }
});

$(document).on("click", "#modal-btn-new, #modal-btn-override", function () {
  if (!oldModeSelected)
    $("#captionContent").val(GenerateWEBVTT());
  
  $("#saveCaptionsModal").modal("hide");
  if (this.id == "modal-btn-override") {
    $("#form_save_captions").find('input[name="file_id"]').val(file_loaded_id);
    updateCaptionsArray($("#captionContent").val());
    send_form_save_captions();
  } else if (this.id == "modal-btn-new") {
    $("#form_save_captions").find('input[name="file_id"]').val("");
    send_form_save_captions();
  }
});

$("#captionFilename").on('input', function (e) {
  file_loaded = false;
  removeFileBtn = $("#remove_file_id_src");
  if (removeFileBtn.length)
    removeFileBtn.click();
});

var send_form_save_captions = function () {
  let fileName = $("#captionFilename").val()
  if (fileName.length == 0) {
    fileName = `${file_prefix}_captions_${Date.now()}`;
  }

  rxSignatureLine = /^WEBVTT(?:\s.*)?$/;
  vttContent = $("#captionContent").val().trim();
  vttLines = vttContent.split(/\r\n|\r|\n/);
  if (!rxSignatureLine.test(vttLines[0])) {
    alert(gettext("Not a valid time track file."));
    return;
  }

  let f = new File([vttContent], fileName + ".vtt", { type: "text/vtt" });
  let data_form = new FormData($("#form_save_captions")[0]);
  data_form.append("folder", current_folder);
  data_form.append("file", f);
  $.ajax({
    url: $("#form_save_captions").attr("action"),
    type: "POST",
    data: data_form,
    processData: false,
    contentType: false,
  })
    .done(function (data) {
      $(data).find("#base-message-alert").appendTo(document.body);
    })
    .fail(function ($xhr) {
      var data = $xhr.status + " : " + $xhr.statustext;
      showalert(
        gettext("error during exchange") +
          "(" +
          data +
          ")<br/>" +
          gettext("no data could be stored."),
        "alert-danger"
      );
    });
};

$("#podvideoplayer").on("error", function (event) {
  var vh = $(this).height();

  // error handling straight from the HTML5 video spec (http://dev.w3.org/html5/spec-author-view/video.html)
  switch (event.originalEvent.target.error.code) {
    case event.originalEvent.target.error.MEDIA_ERR_ABORTED:
      $("#videoError").text("You aborted the video playback.");
      break;
    case event.originalEvent.target.error.MEDIA_ERR_NETWORK:
      $("#videoError").text(
        "A network error caused the video download to fail part-way."
      );
      break;
    case event.originalEvent.target.error.MEDIA_ERR_DECODE:
      $("#videoError").text(
        "The video playback was aborted due to a corruption problem or because the video used features your browser did not support."
      );
      break;
    case event.originalEvent.target.error.MEDIA_ERR_SRC_NOT_SUPPORTED:
      $("#videoError").text(
        "The video could not be loaded, either because the server or network failed or because the format is not supported."
      );
      break;
    default:
      $("#videoError").text("An unknown error occurred.");
      break;
  }
  $("#videoError").height(vh).css("display", "block");
  $(this).css("display", "none");
});

var shortcutsDisplayed = false;
$("#showShortcutTips").on("click", function (e) {
  if (shortcutsDisplayed) {
    $("#shortcutsBlock").hide();
  }
  else {
    $("#shortcutsBlock").show();
  }

  shortcutsDisplayed = !shortcutsDisplayed;
});

$("#clearAllCaptions").on("click", function (e) {
  e.preventDefault();
  var deleteConfirm = confirm(
    gettext("Are you sure you want to delete all caption?")
  );
  if (deleteConfirm) {
    captionsArray.length = 0;
    autoPauseAtTime = -1;

    $("#captionContent").val("");
    $("#captionTitle").html("&nbsp;");
    $("#textCaptionEntry").val("");
    $("#newCaptionsEditor").empty();
  }
});

var oldModeSelected = false;

$("#switchOldEditMode").on("click", function (e) {
  oldModeSelected = !oldModeSelected;

  if (oldModeSelected) {
    $("#captionContent").val(GenerateWEBVTT());
    $("#captionContent").show();
    $("#newCaptionsEditor").hide();
  }
  else {
    $("#captionContent").hide();
    $("#newCaptionsEditor").show();
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
    $("#captionTitle").text(
      "Caption for segment from " +
        FormatTime(theCaption.start) +
        " to " +
        FormatTime(theCaption.end) +
        ":"
    );
    $("#textCaptionEntry").val(theCaption.caption);
    $("#previewTrack").val(theCaption.caption);
  } else {
    $("#captionTitle").html("&nbsp;");
    $("#textCaptionEntry").val("");
    $("#previewTrack").val("");
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
  arr.forEach((text) => {
    if (text.trim().toLowerCase() !== "webvtt") {
      let data = text.split("\n");
      let times = data[0].split("-->");
      newCaption = {
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
    $("#textCaptionEntry").val("").prop("readonly", true).addClass("playing");
    $("#pauseButton").prop("disabled", false);
    $("#playButton, #justSaveCaption, #saveCaptionAndPlay").prop(
      "disabled",
      true
    );
  }, 16);
}

function videoPauseEventHandler() {
  $("#playButton, #justSaveCaption, #saveCaptionAndPlay").prop(
    "disabled",
    false
  );
  $("#textCaptionEntry").removeClass("playing").prop("readonly", false);
  $("#pauseButton").prop("disabled", true);

  var playTime = $("#podvideoplayer").get(0).player.currentTime();
  var captionsEndTime = existingCaptionsEndTime();
  if (playTime - 1 < captionsEndTime) {
    var ci = FindCaptionIndex(playTime - 1);
    if (ci != -1) {
      var theCaption = captionsArray[ci];
      $("#captionTitle").text(
        "Edit caption for segment from " +
          FormatTime(theCaption.start) +
          " to " +
          FormatTime(theCaption.end) +
          ":"
      );
      $("#textCaptionEntry").val(theCaption.caption);
      captionBeingDisplayed = ci;
    } else {
      $("#captionTitle").text("No caption at this time code.");
      $("#textCaptionEntry").val("");
      captionBeingDisplayed = -1;
    }
  } else {
    $("#captionTitle").text(
      "Enter caption for segment from " +
        FormatTime(existingCaptionsEndTime()) +
        " to " +
        FormatTime(playTime) +
        ":"
    );
    $("#textCaptionEntry").val("");
    captionBeingDisplayed = -1;
  }

  $("#textCaptionEntry").focus().get(0).setSelectionRange(1000, 1000); // set focus and selection point to end
}

function videoTimeUpdateEventHandler() {
  var playTime = $("#podvideoplayer").get(0).player.currentTime();
  if (autoPauseAtTime >= 0 && playTime >= autoPauseAtTime) {
    autoPauseAtTime = -1;
    $("#podvideoplayer").get(0).player.pause();
    return;
  }

  var captionsEndTime = existingCaptionsEndTime();
  if (playTime < captionsEndTime) {
    DisplayExistingCaption(playTime);
  } else {
    $("#captionTitle").text(
      "Pause to enter caption for segment from " +
        FormatTime(captionsEndTime) +
        " to " +
        FormatTime(playTime) +
        ":"
    );
    if (captionBeingDisplayed != -1) {
      $("#textCaptionEntry").val("");
      captionBeingDisplayed = -1;
    }
  }
}

//  this enables the demo after a successful video load
function EnableDemoAfterLoadVideo() {
  $(".grayNoVideo, .grayNoVideo a").removeAttr("style");
  $(
    ".grayNoVideo a, .grayNoVideo button, .grayNoVideo input, .grayNoVideo textarea"
  ).prop("disabled", false);
  $("#pauseButton, #saveCaptionAndPlay, #justSaveCaption").prop(
    "disabled",
    true
  ); // these are still disabled
  $("#textCaptionEntry").prop("readonly", true);
}

//  the video element's event handlers
$("#podvideoplayer").bind({
  play: videoPlayEventHandler,
  timeupdate: videoTimeUpdateEventHandler,
  pause: videoPauseEventHandler,
  canplay: EnableDemoAfterLoadVideo,
  loadeddata: EnableDemoAfterLoadVideo, // opera doesn't appear to fire canplay but does fire loadeddata
});

$("#playButton").on("click", function () {
  $("#podvideoplayer").get(0).player.play();
});

$("#pauseButton").on("click", function () {
  $("#podvideoplayer").get(0).player.pause();
});

function GenerateWEBVTT() {
  let vtt = "";
  $('#newCaptionsEditor > .newEditorBlock').each(function() {
    let captionText = this.querySelector('textarea').value;
    let startTime = this.querySelectorAll('a')[0].text;
    let endTime = this.querySelectorAll('a')[1].text;

    vtt += `\n\n${startTime} --> ${endTime}\n${
      captionText
    }`;
  })

  if (vtt.length > 0)
    vtt = "WEBVTT" + vtt;
  
  return vtt;
}

function SaveCurrentCaption() {
  var playTime = $("#podvideoplayer").get(0).player.currentTime();
  var captionsEndTime = existingCaptionsEndTime();
  let new_entry = $("#textCaptionEntry").val();
  if (playTime - 1 < captionsEndTime) {
    var ci = FindCaptionIndex(playTime - 1);
    if (ci != -1) {
      UpdateCaption(ci, new_entry);
    }
  } else {
    AddCaption(captionsEndTime, playTime, new_entry);
  }
}

$("#justSaveCaption").on("click", function () {
  SaveCurrentCaption();
});

$("#saveCaptionAndPlay").on("click", function () {
  SaveCurrentCaption();
  $("#podvideoplayer").get(0).player.play();
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
  $("#captionContent").val(vtt);
};

function UpdateCaption(ci, captionText) {
  captionsArray[ci].caption = captionText;
  updateCaptionHtmlContent();
}

var lastEditedBlock = null;

function CreateCaptionBlock(newCaption) {
  let captionText = newCaption.caption;
  let start = FormatTime(newCaption.start);
  let end = FormatTime(newCaption.end);
  
  let block = {
    // parent
    div: $(`<div class='newEditorBlock'></div>`),

    // textarea
    captionTextInput: $(`<textarea></textarea>`),
    deleteBtn: $(`<button class='caption_block_delete_btn'><i data-feather='trash-2' width='12px' height='12px'></i></button>`),

    // time editable
    timeBlockEditable: $(`<div style='display:none'></div>"`),
    startTimeInput: $(`<input type='text'>`),
    endTimeInput: $(`<input type='text'>`),

    // time links
    timeBlock: $(`<div></div>`),
    startTimeBtn: $(`<a href='#'>${start}</a>`),
    endTimeBtn: $(`<a href='#'>${end}</a>`),

    // flags
    isEditEnabled: false,

    // methods
    enableEdit: function() {
      if (!this.isEditEnabled) {
        if (lastEditedBlock) {
          lastEditedBlock.disableEdit();
        }

        this.startTimeInput.val(
          this.startTimeBtn.text()
        );

        this.endTimeInput.val(
          this.endTimeBtn.text()
        );

        this.timeBlockEditable.css('display', '');
        this.timeBlock.css('display', 'none');

        lastEditedBlock = this;

        this.isEditEnabled = true;
      }
    },

    disableEdit: function() {
      if (this.isEditEnabled) {
        let newStartTime = ParseTime(this.startTimeInput.val());
        let newEndTime = ParseTime(this.endTimeInput.val());

        newCaption.start = newStartTime;
        newCaption.end = newEndTime;

        this.startTimeBtn.text(FormatTime(newStartTime));
        this.endTimeBtn.text(FormatTime(newEndTime));

        this.timeBlockEditable.css('display', 'none');
        this.timeBlock.css('display', '');

        this.isEditEnabled = false;
      }
    },

    delete: function() {
      captionsArray.splice(this.div.index(), 1);
      this.div.remove();
    },

    init: function() {
      this.div.captionBlockObject = this;
      this.captionTextInput.val(captionText);

      this.deleteBtn.click(() => this.delete());
      this.startTimeBtn.click(() => this.enableEdit());
      this.endTimeBtn.click(() => this.enableEdit());
      this.captionTextInput.focus(() => this.enableEdit());

      this.timeBlock.append(this.startTimeBtn, this.endTimeBtn);
      this.timeBlockEditable.append(this.startTimeInput, this.endTimeInput);

      this.div.append(
        this.captionTextInput, 
        this.deleteBtn, 
        this.timeBlock, 
        this.timeBlockEditable
      );

      this.startTimeInput.keypress((e) => {
        if (e.which == 13)
          this.disableEdit();
      });

      this.endTimeInput.keypress((e) => {
        if (e.which == 13)
          this.disableEdit();
      });

      $(document).click((e) => { 
        var target = $(e.target);
        if (!target.closest(this.div).length) 
          this.disableEdit();
      });
    }
  }

  block.init();
  $("#newCaptionsEditor").append(block.div);

  feather.replace();

  block.captionTextInput.bind('input propertychange', function() {
    captionsArray[block.div.index()].caption = this.value;
  });
  
  block.div.hover(function() {
    highlightVideoRegion(newCaption.start, newCaption.end);
  }, function() {
    clearVideoRegion();
  })

  $("#noCaptionsText").remove();
}

// alt+del shortcut
$(document).bind('keydown', function(event) {
  if (event.which === 46 && event.altKey && lastEditedBlock) {
    lastEditedBlock.delete();
  }
});

// pgUp shortcut
$(document).bind('keydown', function(event) {
  if (lastEditedBlock && event.which === 33) {
    let prev = lastEditedBlock.div.prev();
    if (prev) {
      let textarea = prev.find("textarea");
      textarea.focus();
      return false;
    }
  }
});

// pgDown shortcut
$(document).bind('keydown', function(event) {
  if (lastEditedBlock && event.which === 34) {
    let next = lastEditedBlock.div.next();
    if (next) {
      let textarea = next.find("textarea");
      textarea.focus();
      return false;
    }
  }
});

function AddCaptionListRow(ci, newCaption) {
  let vtt = $("#captionContent");
  let vtt_entry = $("#textCaptionEntry").val().trim();
  let start = caption_memories.start_time;
  var end = FormatTime($("#podvideoplayer").get(0).player.currentTime());
  var captionsEndTime = existingCaptionsEndTime();
  let caption_text = `${start} --> ${end}\n${vtt_entry}`;
  if (vtt_entry !== "") {
    if (vtt.val().trim() === "") {
      vtt.val(`WEBVTT\n\n${caption_text}`);
    } else {
      vtt.val(`${vtt.val()}\n\n${caption_text}`);
    }
  }

  CreateCaptionBlock(newCaption);
  caption_memories.start_time = end;
}

function AddCaption(captionStart, captionEnd, captionText) {
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
  return seconds + "." + (sTime.split(".")[1] || 0);
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
      var vid = $("#podvideoplayer").get(0).player;
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

    reader.onload = function () {
      ProcessProxyVttResponse({ status: "success", response: reader.result });
    };

    reader.onerror = function (evt) {
      alert(gettext("Error reading caption file. Code = ") + evt.code);
    };

    try {
      reader.readAsText(fileObject);
    } catch (exc) {
      alert(gettext("Exception thrown reading caption file. Code = ") + exc.code);
    }
  } else {
    alert(gettext("Your browser does not support FileReader."));
  }
}

// invoked by script insertion of proxyvtt.ashx
function ProcessProxyVttResponse(obj) {
  if (obj.status == "error")
    alert(gettext("Error loading caption file: ") + obj.message);
  else if (obj.status == "success") {
    //  delete any captions we've got
    captionsArray.length = 0;
    file_loaded = true;
    file_loaded_id = obj.id_file;
    current_folder = obj.id_folder;

    // strip file extension and set as title
    $("#captionFilename").val(obj.file_name.replace(/\.[^/.]+$/, ""))

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

  $("#newCaptionsEditor").empty();

  var rxTimeLine = /^([\d\.:]+)\s+-->\s+([\d\.:]+)(?:\s.*)?$/;
  var rxCaptionLine = /^(?:<v\s+([^>]+)>)?([^\r\n]+)$/;
  var rxBlankLine = /^\s*$/;
  var rxMarkup = /<[^>]>/g;

  var cueStart = null,
    cueEnd = null,
    cueText = null;

  function appendCurrentCaption() {
    if (cueStart && cueEnd && cueText) {
      newCaption = {
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
  $("#captionContent").val("");
  $("#captionContent").val(vtt);
}

// videojs region highlighting 

var highlightVideoRegion;
var clearVideoRegion;

const registerPlugin = videojs.registerPlugin || videojs.plugin;

const onPlayerReady = function(player, options) {
  var startKeyframe;
  var endKeyframe;
  var regionHighlight;
  
  clearVideoRegion = function() {
    if (startKeyframe)
      startKeyframe.remove()
      
    if (endKeyframe)
      endKeyframe.remove()

    if (regionHighlight)
      regionHighlight.remove()
  }

  highlightVideoRegion = function(startTime, endTime) {
    clearVideoRegion();

    let startPercent = (startTime / player.duration()) * 100;
    let endPercent = (endTime / player.duration()) * 100;

    startKeyframe = $(`<svg class='keyframe keyframe-left' xmlns="http://www.w3.org/2000/svg" width="6" height="11" viewBox="0 0 6 11">
        <path id="Path_4" data-name="Path 4" d="M4.667,0H1.333A1.281,1.281,0,0,0,0,1.222V6.256L6,11V1.222A1.281,1.281,0,0,0,4.667,0Z" fill="#ad327a"/>
      </svg>`);
    startKeyframe.css('left', `${startPercent}%`);
    $(player.controlBar.progressControl.seekBar.playProgressBar.el_).before(startKeyframe);

    regionHighlight = $("<div class='regionHighligh'></div>");
    regionHighlight.css('left', `${startPercent}%`);
    regionHighlight.css('width', `${endPercent - startPercent}%`);
    startKeyframe.after(regionHighlight);

    endKeyframe = $(`<svg class='keyframe keyframe-right' xmlns="http://www.w3.org/2000/svg" width="6" height="11" viewBox="0 0 6 11">
        <path id="Path_5" data-name="Path 5" d="M1.333,0H4.667A1.281,1.281,0,0,1,6,1.222V6.256L0,11V1.222A1.281,1.281,0,0,1,1.333,0Z" fill="#ad327a"/>
      </svg>`);
    endKeyframe.css('left', `${endPercent}%`);
    regionHighlight.after(endKeyframe);
  }
};

const timelineRegions = function(options) {
  this.ready(function() {
    onPlayerReady(this, options);
  });
};

registerPlugin('timelineRegions', timelineRegions);

videojs.hook('setup', function(player) {
  player.timelineRegions();
});