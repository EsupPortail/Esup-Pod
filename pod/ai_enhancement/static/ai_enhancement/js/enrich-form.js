/**
 * @file Esup-Pod functions for enrich-form.
 */


const BORDER_CLASS = 'border-d';

const ENRICH_INPUT_SELECTED = 'enrich-input-selected';


function decodeString(str) {
  return str.replace(/&#x([0-9A-Fa-f]+);/g, (match, p1) => String.fromCharCode(parseInt(p1, 16)));
}


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


function addEventListeners(videoSlug, videoTitle, videoDescription) {
  const elements = [
    'title',
    'description',
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
            break;
          case 'description':
            if (videoDescription.length > 0) {
              initialVersionElement.children[0].textContent = decodeString(videoDescription);
            } else {
              initialVersionElement.children[0].textContent = gettext('No description');
              initialVersionElement.children[0].style.color = 'grey';
              initialVersionElement.children[0].style.fontStyle = 'italic';
              initialVersionElement.children[0].classList.add('no-content');
            }
            aiVersionElement.children[0].textContent = response['enrichmentVersionMetadata']['description'];
            break;
        }
        togglePairInput(aiVersionElement, initialVersionElement, input, element);
        initialVersionElement.addEventListener('click', () => {
          let input = document.getElementById('id_' + element);
          togglePairInput(initialVersionElement, aiVersionElement, input, element);
        });
        aiVersionElement.addEventListener('click', () => {
          let input = document.getElementById('id_' + element);
          togglePairInput(aiVersionElement, initialVersionElement, input, element);
        })
        input.addEventListener('input', () => {
          initialVersionElement.children[0].classList.add(BORDER_CLASS);
          initialVersionElement.children[0].classList.remove(ENRICH_INPUT_SELECTED);
          aiVersionElement.children[0].classList.remove(ENRICH_INPUT_SELECTED);
          aiVersionElement.children[0].classList.add(BORDER_CLASS);
        });
      }
    })
    .catch(err => console.error('An error occurred: '+ err));  // TODO Make a real error
}
