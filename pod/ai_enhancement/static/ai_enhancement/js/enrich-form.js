/**
 * @file Esup-Pod functions for enrich-form.
 *
 * @since 3.7.0
 */

// Read-only globals defined in main.js
/* global decodeString remove_quotes removeAccentsAndLowerCase */

const BORDER_CLASS = 'border-d';

const ENRICH_INPUT_SELECTED = 'enrich-input-selected';

const TAGS_PER_LINE = 4;


/**
 * Select the element to select and unselect the element to unselect.
 *
 * @param {HTMLElement} elementToSelect The element to select.
 * @param {HTMLElement} elementToUnselect The element to unselect.
 */
function selectElement(elementToSelect, elementToUnselect) {
  elementToSelect.classList.remove(BORDER_CLASS);
  elementToSelect.classList.add(ENRICH_INPUT_SELECTED);
  elementToUnselect.classList.remove(ENRICH_INPUT_SELECTED);
  elementToUnselect.classList.add(BORDER_CLASS);
}


/**
 * Toggle the input and the two versions of the element.
 *
 * @param {HTMLElement} selectedElement The selected element.
 * @param {HTMLElement} notSelectedElement The not selected element.
 * @param {HTMLElement} input The input element.
 * @param {string} elementName The name of the element.
 */
function togglePairInput(selectedElement, notSelectedElement, input, elementName) {
  selectElement(selectedElement.children[0], notSelectedElement.children[0]);
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


/**
 * Toggle the input and the multiple versions of the element.
 *
 * @param {HTMLElement} selectedElement The selected element.
 * @param {HTMLElement} notSelectedElement The not selected element.
 * @param {HTMLElement} input The input element.
 */
function toggleMultiplePairInput(selectedElement, notSelectedElement, input) {
  selectElement(selectedElement.children[0], notSelectedElement.children[0]);
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
 * @param {HTMLElement} aiVersionElement The AI version of the element.
 * @param {HTMLElement} initialVersionElement The initial version of the element.
 * @param {HTMLElement} input The input element.
 * @param {string} element The name of the element.
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
  });
  input.addEventListener('input', () => event__inputChange(initialVersionElement, aiVersionElement));
}


/**
 * This function is called when the input is changed.
 *
 * @param {HTMLElement} initialVersionElement The initial version of the element.
 * @param {HTMLElement} aiVersionElement The AI version of the element.
 */
function event__inputChange(initialVersionElement, aiVersionElement) {
  initialVersionElement.children[0].classList.add(BORDER_CLASS);
  initialVersionElement.children[0].classList.remove(ENRICH_INPUT_SELECTED);
  aiVersionElement.children[0].classList.remove(ENRICH_INPUT_SELECTED);
  aiVersionElement.children[0].classList.add(BORDER_CLASS);
}


/**
 * Add the tags elements to the tags container.
 *
 * @param {string[]} tags The list of tags.
 * @param {HTMLElement} input The input element.
 */
function addTagsElements(tags, input) {
  const tagsContainerElement = document.getElementById('tags-container');
  let tagLineElement = tagsContainerElement.children[tagsContainerElement.children.length - 1];
  for (let i = 0; i < tags.length; i++) {
    if (i % TAGS_PER_LINE === 0 && i !== 0) {
      tagLineElement = document.createElement('div');
      tagLineElement.classList.add('row');
      tagsContainerElement.appendChild(tagLineElement);
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
 * @param {HTMLElement} element The element to set the information.
 * @param {string} value The value to set in the element.
 * @param {string} message The message to set in the element if the value is empty.
 */
function setInformationOrEmptyString(element, value, message) {
  if (value.length > 0) {
    element.children[0].innerHTML = decodeString(value);
  } else {
    element.children[0].textContent = gettext(message);
    element.children[0].classList.add('text-muted', 'font-italic', 'no-content');
  }
}


/**
 * Add event listeners to the elements.
 *
 * @param {string} videoSlug The video slug.
 * @param {string} videoTitle The video title.
 * @param {string} videoDescription The video description.
 * @param {string} videoDiscipline The video discipline.
 * @param {string} json_url The url to fetch to get json information.
 */
function addEventListeners(videoSlug, videoTitle, videoDescription, videoDiscipline, json_url) {
  const elements = [
    'title',
    'description',
    'tags',
    'disciplines',
  ];
  const options = {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  };
  fetch(json_url, options)
    .then(response => response.json())
    .then(response => {
      for (let element of elements) {
        let initialVersionElement = document.getElementById('initial-version-' + element);
        let aiVersionElement = document.getElementById('ai-version-' + element);
        let input = document.getElementById('id_' + element);
        switch (element) {
          case 'title':
            initialVersionElement.children[0].textContent = decodeString(videoTitle);
            aiVersionElement.children[0].textContent = remove_quotes(response['enrichmentVersionMetadata']['title']);
            addTogglePairInput(aiVersionElement, initialVersionElement, input, element);
            break;
          case 'description':
            setInformationOrEmptyString(initialVersionElement, videoDescription, gettext('No description'));
            aiVersionElement.children[0].textContent = response['enrichmentVersionMetadata']['description'];
            addTogglePairInput(aiVersionElement, initialVersionElement, input, element);
            break;
          case 'tags':
            const topics = response['enrichmentVersionMetadata']['topics'];
            const newTopics = [];
            const tagInput = document.getElementById('id_tags');
            for (let i = 0; i < topics.length; i++) {
              if (!tagInput.value.includes(removeAccentsAndLowerCase(topics[i]))) {
                newTopics.push(topics[i]);
              }
            }
            addTagsElements(newTopics, input);
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
            });
            input.addEventListener('input', () => event__inputChange(initialVersionElement, aiVersionElement));
            break;
        }
      }
    })
    .catch(err => showalert(gettext("An error has occurred. Please try later."), 'alert-danger'));
}
