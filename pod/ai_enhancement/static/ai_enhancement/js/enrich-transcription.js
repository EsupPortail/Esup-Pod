/**
 * @file Esup-Pod functions for enrich-transcription.
 */


function addSubtitles(captionText, startTime, endTime, initialCodeNumber) {
  const newCaptionsEditor = document.getElementById('newCaptionsEditor');
  if (newCaptionsEditor) {
    if (captionText.length > 80) {
      addSubtitles(captionText.substring(0, 80), startTime, endTime, initialCodeNumber);
      startTime += .1;
      captionText = captionText.substring(80);
    }
    let formattedStartTime = convertTime(startTime)['formattedOutput'];
    let formattedEndTime = convertTime(endTime)['formattedOutput'];
    const htmlCode = `
      <form class="newEditorBlock row">
        <div class="captionButtons col-1 d-flex flex-wrap align-items-center">
          <button type="button" class="btn btn-light" title="Ajouter un(e) légende/sous-titre ci-dessous" aria-label="Ajouter">
            <i class="bi bi-plus-circle" aria-hidden="true"></i>
          </button>
          <button type="button" class="btn btn-light" title="Supprimer ce(tte) légende/sous-titre" aria-label="Supprimer">
            <i class="bi bi-x-circle" aria-hidden="true"></i>
          </button>
        </div>
        <div class="captionText col">
          <label for="c${initialCodeNumber}=">Légende / Sous-titre</label>
          <textarea class="captionTextInput form-control" cols="40" rows="2" wrap="hard" maxlength="80" name="captionTextInput" required="" id="c${initialCodeNumber}">${captionText.trim()}</textarea>
        </div>
        <div class="captionTimestamps col-sm-3 col-md-2">
          <span>Horodatages</span>
          <a class="startTimeBtn btn-link" href="#podvideoplayer">${formattedStartTime}</a>
          <a class="endTimeBtn btn-link" href="#podvideoplayer">${formattedEndTime}</a>
        </div>
        <div class="captionTimestamps col-3" style="display:none">
          <label class="p-2" for="start_c${initialCodeNumber}">Début</label>
          <input class="form-control" type="text" pattern="([0-9][0-9]:){0,1}([0-5][0-9]:){0,1}[0-5][0-9].([0-9]){3}" value="${formattedStartTime}" required="" id="start_c${initialCodeNumber}">
          <label class="p-2" for="end_c${initialCodeNumber}">Fin</label>
          <input class="form-control" type="text" pattern="([0-9][0-9]:){0,1}([0-5][0-9]:){0,1}[0-5][0-9].([0-9]){3}" value="${formattedEndTime}" required="" id="end_c${initialCodeNumber}">
        </div>
      </form>
    `;
    const noCaptionsText = document.getElementById('noCaptionsText');
    if (noCaptionsText) {
      noCaptionsText.remove();
      newCaptionsEditor.innerHTML = htmlCode;
    } else {
      newCaptionsEditor.innerHTML += htmlCode;
    }
  } else {
    showalert(gettext('An error occurred when adding the caption/subtitles. Please try later.'), 'alert-danger');
  }
}


/**
 * Set the language select to the given language code.
 *
 * @param languageCode {string} The language code to set the select to.
 */
function setLanguageSelect(languageCode) {
  const captionLanguageSelect = document.getElementById('captionLanguageSelect');
  captionLanguageSelect.value = languageCode;
}


/**
 * Convert seconds to minutes, seconds and milliseconds.
 *
 * @param seconds {number} The seconds to convert.
 *
 * @return {{milliseconds: number, seconds: number, minutes: number}}
 */
function convertTime(seconds) {
  let minutes = Math.floor(seconds / 60);
  let remainingSeconds = Math.floor(seconds % 60);
  let milliseconds = Math.floor((seconds - Math.floor(seconds)) * 1000);
  let formattedOutput = `${padZero(minutes, 2)}:${padZero(remainingSeconds, 2)}.${padZero(milliseconds, 3)}`;
  return {
    minutes: minutes,
    seconds: remainingSeconds,
    milliseconds: milliseconds,
    formattedOutput: formattedOutput,
  };
}


/**
 * Pad a number with zeros.
 *
 * @param number {number} The number to pad.
 * @param length {number} The length of the result.
 *
 * @return {string} The padded number.
 */
function padZero(number, length) {
  return ('0'.repeat(length) + number).slice(-length);
}


function loadSubtitles(videoSlug) {
  const captionKindSelect = document.getElementById('captionKindSelect');
  const options = {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  };
  let initialCodeNumber = 85393643;
  captionKindSelect.selectedIndex = 'subtitles';
  fetch(`http://${window.location.host}/ai-enhancement/enrich-video/${videoSlug}/json/`, options)
    .then(response => response.json())
    .then(response => {
      setLanguageSelect(response['transcript']['language']);
      for (let sentence of response['transcript']['sentences']) {
        addSubtitles(
          sentence['text'],
          sentence['start'],
          sentence['end'],
          initialCodeNumber,
        );
        initialCodeNumber += 1;
      }
    })
    .catch(error => console.error('An error occurred: ', error));
}
