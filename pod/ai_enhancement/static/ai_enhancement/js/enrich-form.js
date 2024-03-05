/**
 * @file Esup-Pod functions for enrich-form.
 */


const BORDER_CLASS = 'border-d';

const ENRICH_INPUT_SELECTED = 'enrich-input-selected';

const TAGS_PER_LINE = 10;


/**
 * Decode the string from the HTML entity.
 *
 * @param str {string} The string to decode.
 *
 * @return {string} The decoded string.
 */
function decodeString(str) {
  str = str.replace(/&#x([0-9A-Fa-f]+);/g, (match, p1) => String.fromCharCode(parseInt(p1, 16)));
  str = str.replace(/&#(\d+);/g, (match, p1) => String.fromCharCode(parseInt(p1, 10)));
  return str;
}


/**
 * Toggle the input and the two versions of the element.
 *
 * @param selectedElement {HTMLElement} The selected element.
 * @param notSelectedElement {HTMLElement} The not selected element.
 * @param input {HTMLElement} The input element.
 * @param elementName {string} The name of the element.
 */
function togglePairInput(selectedElement, notSelectedElement, input, elementName) {
  selectedElement.children[0].classList.remove(BORDER_CLASS);
  selectedElement.children[0].classList.add(ENRICH_INPUT_SELECTED);
  notSelectedElement.children[0].classList.remove(ENRICH_INPUT_SELECTED);
  notSelectedElement.children[0].classList.add(BORDER_CLASS);
  let newString = selectedElement.children[0].textContent.trim();
  switch (elementName) {
    case 'title':
      input.value = newString;
      break;
    case 'description':
      if (!selectedElement.children[0].classList.contains('no-content')) {
        input.value = newString;
      } else {
        input.value = '';
      }
      break;
  }
}


function toggleMultiplePairInput(selectedElement, notSelectedElement, input) {
  selectedElement.children[0].classList.remove(BORDER_CLASS);
  selectedElement.children[0].classList.add(ENRICH_INPUT_SELECTED);
  notSelectedElement.children[0].classList.remove(ENRICH_INPUT_SELECTED);
  notSelectedElement.children[0].classList.add(BORDER_CLASS);
  let newString = selectedElement.children[0].textContent.trim();
  if (newString === gettext('No discipline')) {
    input.value = '';
  } else {
    for (let i = 0; i < input.options.length; i++) {
      if (input.options[i].text === newString) {
        input.value = input.options[i].value;
        break;
      }
    }
  }
}


/**
 * Add event listeners to the input and the two versions of the element.
 *
 * @param aiVersionElement {HTMLElement} The AI version of the element.
 * @param initialVersionElement {HTMLElement} The initial version of the element.
 * @param input {HTMLElement} The input element.
 * @param element {string} The name of the element.
 */
function addTogglePairInput(aiVersionElement, initialVersionElement, input, element) {
  togglePairInput(aiVersionElement, initialVersionElement, input, element);
  initialVersionElement.addEventListener('click', () => {
    let input = document.getElementById('id_' + element);
    togglePairInput(initialVersionElement, aiVersionElement, input, element);
  });
  aiVersionElement.addEventListener('click', () => {
    let input = document.getElementById('id_' + element);
    togglePairInput(aiVersionElement, initialVersionElement, input, element);
  })
  input.addEventListener('input', () => event__inputChange(initialVersionElement, aiVersionElement));
}


/**
 * This function is called when the input is changed.
 *
 * @param initialVersionElement {HTMLElement} The initial version of the element.
 * @param aiVersionElement {HTMLElement} The AI version of the element.
 */
function event__inputChange(initialVersionElement, aiVersionElement) {
  initialVersionElement.children[0].classList.add(BORDER_CLASS);
  initialVersionElement.children[0].classList.remove(ENRICH_INPUT_SELECTED);
  aiVersionElement.children[0].classList.remove(ENRICH_INPUT_SELECTED);
  aiVersionElement.children[0].classList.add(BORDER_CLASS);
}


function addTagsElements(tags, input) {
  const tagsContainerElement = document.getElementById('tags-container');
  let tagLineElement = tagsContainerElement.children[tagsContainerElement.children.length - 1];
  for (let i = 0; i < tags.length; i++) {
    if (i % TAGS_PER_LINE === 0 && i !== 0) {
      tagLineElement = document.createElement('div');
      tagLineElement.classList.add('row');
      tagsContainerElement.textContent = tagLineElement.innerHTML;
    }
    const tagElement = document.createElement('div');
    tagElement.classList.add('col');
    const selectableElement = document.createElement('div');
    selectableElement.classList.add('border-d', 'rounded-4', 'p-3', 'mb-3', 'mt-3', 'blockquote');
    selectableElement.textContent = tags[i];
    tagElement.addEventListener('click', () => {
      selectableElement.classList.add(ENRICH_INPUT_SELECTED);
      if (input.value.length > 0) {
        input.value += ` "${tags[i]}"`;
      } else {
        input.value = `"${tags[i]}"`;
      }
      tagElement.remove();
    });
    tagElement.appendChild(selectableElement);
    tagLineElement.appendChild(tagElement);
  }
  const tagsInformationsElement = document.getElementById('tags-informations-text');
  if (tagsInformationsElement) {
    tagsInformationsElement.remove();
  }
}


/**
 * Set the information or an empty string in the element.
 *
 * @param element {HTMLElement} The element to set the information.
 * @param value {string} The value to set in the element.
 * @param message {string} The message to set in the element if the value is empty.
 */
function setInformationOrEmptyString(element, value, message) {
  if (value.length > 0) {
    element.children[0].innerHTML = decodeString(value);
  } else {
    element.children[0].textContent = gettext(message);
    element.children[0].style.color = 'grey';
    element.children[0].style.fontStyle = 'italic';
    element.children[0].classList.add('no-content');
  }
}


function addEventListeners(videoSlug, videoTitle, videoDescription, videoDiscipline) {
  const elements = [
    'title',
    'description',
    'tags',
    'disciplines',
  ]
  const options = {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  };
  fetch(`http://${window.location.host}/ai-enhancement/enrich-video/${videoSlug}/json/`, options)
    .then(response => response.json())
    .then(response => {
      for (let element of elements) {
        let initialVersionElement = document.getElementById('initial-version-' + element);
        let aiVersionElement = document.getElementById('ai-version-' + element);
        let input = document.getElementById('id_' + element);
        switch (element) {
          case 'title':
            initialVersionElement.children[0].textContent = decodeString(videoTitle);
            aiVersionElement.children[0].textContent = response['enrichmentVersionMetadata']['title'];
            addTogglePairInput(aiVersionElement, initialVersionElement, input, element);
            break;
          case 'description':
            setInformationOrEmptyString(initialVersionElement, videoDescription, gettext('No description'));
            aiVersionElement.children[0].textContent = response['enrichmentVersionMetadata']['description'];
            addTogglePairInput(aiVersionElement, initialVersionElement, input, element);
            break;
          case 'tags':
            addTagsElements(response['enrichmentVersionMetadata']['topics'], input);
            break;
          case 'disciplines':
            setInformationOrEmptyString(initialVersionElement, videoDiscipline, gettext('No discipline'));
            aiVersionElement.children[0].textContent = response['enrichmentVersionMetadata']['discipline'];
            toggleMultiplePairInput(aiVersionElement, initialVersionElement, input);
            initialVersionElement.addEventListener('click', () => {
              toggleMultiplePairInput(initialVersionElement, aiVersionElement, input);
            });
            aiVersionElement.addEventListener('click', () => {
              toggleMultiplePairInput(aiVersionElement, initialVersionElement, input);
            })
            input.addEventListener('input', () => event__inputChange(initialVersionElement, aiVersionElement));
            break;
        }
      }
    })
    .catch(err => showalert(gettext("An error has occurred. Please try later."), 'alert-danger'));
}