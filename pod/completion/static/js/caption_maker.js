$(document).on('click', 'a.file-name', function() {
    let url = '/podfile/get_file/file/'; 
    let data_form = $("#captionmaker_form" ).serializeArray();
    send_form_data(url, data_form, "ProcessProxyVttResponse");
})

$(document).on('submit', '#form_save_captions', function(e) {
    e.preventDefault();
    if (!(captionsArray.length)) {
        showalert(gettext("There is no captions to save"), "alert-danger");
        return;
    }
    if (typeof(file_loaded) != "undefined" && file_loaded) {
        $("#saveCaptionsModal").modal('show');
    }
    else {
        $(this).find('input[name="file_id"]').val("");
        let href = window.location.href.split('/');
        send_form_save_captions(href[href.length - 2] + '_captions_' + Date.now());
    }
})

$(document).on('click', '#modal-btn-new, #modal-btn-override', function() {
    $("#saveCaptionsModal").modal('hide');
    if (this.id == 'modal-btn-override') {
        $('#form_save_captions').find('input[name="file_id"]').val(file_loaded_id);
        //alert($('#fileinput_id_src').find('strong').find('a').html());
        //alert($('#fileinput_id_src').text().trim());
        send_form_save_captions($('#fileinput_id_src').text().trim());
    }
    else if (this.id == 'modal-btn-new') {
        $('#form_save_captions').find('input[name="file_id"]').val("");
        let href = window.location.href.split('/');
        send_form_save_captions(href[href.length - 2] + '_captions_' + Date.now());
    }
})

var send_form_save_captions = function(name) {
    rxSignatureLine = /^WEBVTT(?:\s.*)?$/;
    vttContent = CreateVTTSource();
    vttLines = vttContent.split(/\r\n|\r|\n/);
    if (!rxSignatureLine.test(vttLines[0])) {
        alert("Not a valid time track file.");
        return;
    }
    let n = name 
    let f = new File([vttContent], n + '.vtt', {type: 'text/vtt'});
    let data_form = new FormData($('#form_save_captions')[0]);
    data_form.append('folder', current_folder);
    data_form.append('file', f);
    $.ajax({
        url: $("#form_save_captions").attr("action"), 
        type: 'POST',
        data: data_form,
        processData: false,
        contentType: false                    
    }).done(function(data){
        $(data).find('#base-message-alert').appendTo(document.body);
    }).fail(function($xhr){
        var data = $xhr.status+ " : " +$xhr.statustext;
        showalert(gettext("error during exchange") + "("+data+")<br/>"+gettext("no data could be stored."), "alert-danger");
    });
}

$('#podvideoplayer').on('error', function(event) {
    var vh = $(this).height();

    // error handling straight from the HTML5 video spec (http://dev.w3.org/html5/spec-author-view/video.html)
    switch (event.originalEvent.target.error.code) {
    case event.originalEvent.target.error.MEDIA_ERR_ABORTED:
        $("#videoError").text("You aborted the video playback.");
        break;
    case event.originalEvent.target.error.MEDIA_ERR_NETWORK:
        $("#videoError").text("A network error caused the video download to fail part-way.");
        break;
    case event.originalEvent.target.error.MEDIA_ERR_DECODE:
        $("#videoError").text("The video playback was aborted due to a corruption problem or because the video used features your browser did not support.");
        break;
    case event.originalEvent.target.error.MEDIA_ERR_SRC_NOT_SUPPORTED:
        $("#videoError").text("The video could not be loaded, either because the server or network failed or because the format is not supported.");
        break;
    default:
        $("#videoError").text("An unknown error occurred.");
        break;
    }
    $("#videoError").height(vh).css("display", "block");
    $(this).css("display", "none");
});

$('#clearAllCaptions').on('click', function () {
    var deleteConfirm = confirm(gettext("Are you sure you want to delete all caption ?"));
    if (deleteConfirm){
        captionsArray.length = 0;
        autoPauseAtTime = -1;
        $("#display div").remove();
        $("#captionTitle").html("&nbsp;");
        $("#textCaptionEntry").val("");
    }
});

//  index into captionsArray of the caption being displayed. -1 if none.
var captionBeingDisplayed = -1;

function DisplayExistingCaption(seconds) {
    var ci = FindCaptionIndex(seconds);
    if (ci != captionBeingDisplayed) {
        captionBeingDisplayed = ci;
        if (ci != -1) {
            var theCaption = captionsArray[ci];
            $("#captionTitle").text("Caption for segment from " + FormatTime(theCaption.start) + " to " + FormatTime(theCaption.end) + ":");
            $("#textCaptionEntry").val(theCaption.caption);
        } else {
            $("#captionTitle").html("&nbsp;");
            $("#textCaptionEntry").val("");
        }
    }
}

function existingCaptionsEndTime() {
    return captionsArray.length > 0 ? captionsArray[captionsArray.length - 1].end : 0;
}

function videoPlayEventHandler() {
    captionBeingDisplayed = -1;
    //  give Opera a beat before doing this
    window.setTimeout(function() {
        $("#textCaptionEntry").val("").prop("readonly", true).addClass("playing");
        $("#pauseButton").prop("disabled", false);
        $("#playButton, #justSaveCaption, #saveCaptionAndPlay").prop("disabled", true);
    }, 16);
}

function videoPauseEventHandler() {
    $("#playButton, #justSaveCaption, #saveCaptionAndPlay").prop("disabled", false);
    $("#textCaptionEntry").removeClass("playing").prop("readonly", false);
    $("#pauseButton").prop("disabled", true);

    var playTime = $('#podvideoplayer').get(0).player.currentTime();
    var captionsEndTime = existingCaptionsEndTime();
    if (playTime - 1 < captionsEndTime) {
        var ci = FindCaptionIndex(playTime - 1);
        if (ci != -1) {
            var theCaption = captionsArray[ci];
            $("#captionTitle").text("Edit caption for segment from " + FormatTime(theCaption.start) + " to " + FormatTime(theCaption.end) + ":");
            $("#textCaptionEntry").val(theCaption.caption);
            captionBeingDisplayed = ci;
        } else {
            $("#captionTitle").text("No caption at this time code.");
            $("#textCaptionEntry").val("");
            captionBeingDisplayed = -1;
        }
    } else {
        $("#captionTitle").text("Enter caption for segment from " + FormatTime(existingCaptionsEndTime()) + " to " + FormatTime(playTime) + ":");
        $("#textCaptionEntry").val("");
        captionBeingDisplayed = -1;
    }

    $("#textCaptionEntry").focus().get(0).setSelectionRange(1000, 1000); // set focus and selection point to end
}

function videoTimeUpdateEventHandler() {
    var playTime = $('#podvideoplayer').get(0).player.currentTime();
    if (autoPauseAtTime >= 0 && playTime >= autoPauseAtTime) {
        autoPauseAtTime = -1;
        $('#podvideoplayer').get(0).player.pause();
        return;
    }

    var captionsEndTime = existingCaptionsEndTime();
    if (playTime < captionsEndTime) {
        DisplayExistingCaption(playTime);
    } else {
        $("#captionTitle").text("Pause to enter caption for segment from " + FormatTime(captionsEndTime) + " to " + FormatTime(playTime) + ":");
        if (captionBeingDisplayed != -1) {
            $("#textCaptionEntry").val("");
            captionBeingDisplayed = -1;
        }
    }
}

//  this enables the demo after a successful video load
function EnableDemoAfterLoadVideo() {
    $(".grayNoVideo, .grayNoVideo a").removeAttr("style");
    $(".grayNoVideo a, .grayNoVideo button, .grayNoVideo input, .grayNoVideo textarea").prop("disabled", false);
    $("#pauseButton, #saveCaptionAndPlay, #justSaveCaption").prop("disabled", true); // these are still disabled
    $("#textCaptionEntry").prop("readonly", true);
}

//  the video element's event handlers
$('#podvideoplayer').bind({
    play: videoPlayEventHandler,
    timeupdate: videoTimeUpdateEventHandler,
    pause: videoPauseEventHandler,
    canplay: EnableDemoAfterLoadVideo,
    loadeddata: EnableDemoAfterLoadVideo    // opera doesn't appear to fire canplay but does fire loadeddata
});

$("#playButton").on('click',function() {
    $('#podvideoplayer').get(0).player.play();
});

$("#pauseButton").on('click',function() {
    $('#podvideoplayer').get(0).player.pause();
});

function SaveCurrentCaption() {
    var playTime = $('#podvideoplayer').get(0).player.currentTime();
    var captionsEndTime = existingCaptionsEndTime();
    if (playTime - 1 < captionsEndTime) {
        var ci = FindCaptionIndex(playTime - 1);
        if (ci != -1) {
            UpdateCaption(ci, $("#textCaptionEntry").val());
        }
    } else {
        AddCaption(captionsEndTime, playTime, $("#textCaptionEntry").val());
    }
}

$("#justSaveCaption").on('click',function() {
    SaveCurrentCaption();
});

$("#saveCaptionAndPlay").on('click',function() {
    SaveCurrentCaption();
    $('#podvideoplayer').get(0).player.play();
});

function UpdateCaption(ci, captionText) {
    captionsArray[ci].caption = captionText;
    $("#ci" + ci.toString() + " span:last-child").html(XMLEncode(captionText).replace(/\r\n|\r|\n/g, "<br/>"));
}

function AddCaptionListRow(ci) {
    var theId = "ci" + ci.toString();
    $("#display").append("<div id=\"" + theId + "\"><span>" + FormatTime(captionsArray[ci].start) + "</span><span>" + FormatTime(captionsArray[ci].end) + "</span><span>" + XMLEncode(captionsArray[ci].caption).replace(/\r\n|\r|\n/g, "<br/>") + "</span></div>");
    $("#" + theId).click(function () {
        PlayCaptionFromList($(this).attr("id"));
    });
}

function AddCaptionListRow(ci) {
    var theId = "ci" + ci.toString();
    $("#display").append("<div id=\"" + theId + "\"><span>" + FormatTime(captionsArray[ci].start) + "</span><span>" + FormatTime(captionsArray[ci].end) + "</span><span>" + XMLEncode(captionsArray[ci].caption).replace(/\r\n|\r|\n/g, "<br/>") + "</span></div>");
    $("#" + theId).click(function () {
        PlayCaptionFromList($(this).attr("id"));
    });
}

function AddCaption(captionStart, captionEnd, captionText) {
    captionsArray.push({ start: captionStart, end: captionEnd, caption: Trim(captionText) });
    AddCaptionListRow(captionsArray.length - 1);
    //RefreshCaptionFileDisplay();
}

function SortAndDisplayCaptionList() {
    captionsArray.sort(function(a, b) {
        return a.start - b.start;
    });
    $("#display div").remove();
    for (var ci = 0; ci < captionsArray.length; ++ci) {
        AddCaptionListRow(ci);
    }
}

function Trim(s) {
    return s.replace(/^\s+|\s+$/g, "");
}

//  parses webvtt time string format into floating point seconds
function ParseTime(sTime) {
    //  parse time formatted as hours:mm:ss.sss where hours are optional
    if (sTime) {
        var m = sTime.match( /^\s*(\d+)?:?(\d+):([\d\.]+)\s*$/ );
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
    return 0;
}

//  formats floating point seconds into the webvtt time string format
function FormatTime(seconds) {
    var hh = Math.floor(seconds / (60 * 60));
    var mm = Math.floor(seconds / 60) % 60;
    var ss = seconds % 60;
    return (hh == 0 ? "" : (hh < 10 ? "0" : "") + hh.toString() + ":") + (mm < 10 ? "0" : "") + mm.toString() + ":" + (ss < 10 ? "0" : "") + ss.toFixed(3);
}

//  our state
// var file_loaded = false;
// var file_loaded_id = undefined;
// var file_loaded_folder_id = undefined;
// var captionsArray = [];
// var autoPauseAtTime = -1;

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

function PlayCaptionFromList(listRowId) {
    var captionsArrayIndex = parseInt(listRowId.match(/ci(\d+)/)[1]);

    var vid = $('#podvideoplayer').get(0).player;
    // vid.pause();
    vid.currentTime(captionsArray[captionsArrayIndex].start);
    autoPauseAtTime = captionsArray[captionsArrayIndex].end;
    vid.play();
}

function CreateVTTSource() {
    var s = "WEBVTT\r\n\r\n";
    for (var i = 0; i < captionsArray.length; ++i) {
        if (captionsArray[i].caption != "") {
            s += (FormatTime(captionsArray[i].start) + " --> " + FormatTime(captionsArray[i].end) + "\r\n");
            s += captionsArray[i].caption + "\r\n\r\n";
        }
    }
    return s;
}

// var captionFileSourceUpdateTimer = null;

function XMLEncode(s) {     
    return s.replace(/\&/g, '&amp;').replace(/“/g, '&quot;').replace(/”/g,'&quot;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');   //.replace(/'/g, '&apos;').replace(/"/g, '&quot;');
}

function XMLDecode(s) {
    return s.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&apos;/g, "'").replace(/&quot;/g, '"').replace(/&amp;/g, '&');
}

function LoadCaptionFile(fileObject) {
    if (window.FileReader) {
        var reader = new window.FileReader();

        reader.onload = function() {
            ProcessProxyVttResponse({ status: "success", response: reader.result });
        };

        reader.onerror = function(evt) {
            alert("Error reading caption file. Code = " + evt.code);
        };

        try {
            reader.readAsText(fileObject);
        } catch(exc) {
            alert("Exception thrown reading caption file. Code = " + exc.code);
        }
    } else {
        alert("Your browser does not support FileReader.");
    }
}

//  invoked by script insertion of proxyvtt.ashx
function ProcessProxyVttResponse(obj) {
    if (obj.status == "error")
        alert("Error loading caption file: " + obj.message);
    else if (obj.status == "success") {
        //  delete any captions we've got
        captionsArray.length = 0;
        file_loaded = true;
        file_loaded_id = obj.id_file;
        current_folder = obj.id_folder;
        if (obj.response.indexOf("WEBVTT") == 0) {
            ParseAndLoadWebVTT(obj.response);
        } else {
            alert("Unrecognized caption file format.");
        }
    }
}

//-----------------------------------------------------------------------------------------------------------------------------------------
//  Partial parser for WebVTT files based on the spec at http://dev.w3.org/html5/webvtt/
//-----------------------------------------------------------------------------------------------------------------------------------------

function ParseAndLoadWebVTT(vtt) {

    var rxSignatureLine = /^WEBVTT(?:\s.*)?$/;

    var vttLines = vtt.split(/\r\n|\r|\n/); // create an array of lines from our file

    if (!rxSignatureLine.test(vttLines[0])) { // must start with a signature line
        alert("Not a valid time track file.");
        return;
    }

    var rxTimeLine = /^([\d\.:]+)\s+-->\s+([\d\.:]+)(?:\s.*)?$/;
    var rxCaptionLine = /^(?:<v\s+([^>]+)>)?([^\r\n]+)$/;
    var rxBlankLine = /^\s*$/;
    var rxMarkup = /<[^>]>/g;

    var cueStart = null, cueEnd = null, cueText = null;

    function appendCurrentCaption() {
        if (cueStart && cueEnd && cueText) {
            captionsArray.push({ start: cueStart, end: cueEnd, caption: Trim(cueText) });
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
            if(cueStart==0) cueStart = "0.0";
            cueEnd = ParseTime(timeMatch[2]);
            continue;
        }

        var captionMatch = rxCaptionLine.exec(vttLines[i]);
        if (captionMatch && cueStart && cueEnd) {
            //  captionMatch[1] is the optional voice (speaker) we're ignoring
            var capLine = captionMatch[2].replace(rxMarkup, "");
            if (cueText)
                cueText += " " + capLine;
            else {
                cueText = capLine;
            }
        }
    }
    appendCurrentCaption();
    SortAndDisplayCaptionList();
}
