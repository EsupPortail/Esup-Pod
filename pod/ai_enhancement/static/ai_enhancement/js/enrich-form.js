/**
 * @file Esup-Pod functions for enrich-form.
 */


const BORDER_CLASS = 'border-d';

const ENRICH_INPUT_SELECTED = 'enrich-input-selected';


function togglePairInput(selectedElement, notSelectedElement, input) {
  selectedElement.classList.remove(BORDER_CLASS);
  selectedElement.classList.add(ENRICH_INPUT_SELECTED);
  notSelectedElement.classList.remove(ENRICH_INPUT_SELECTED);
  notSelectedElement.classList.add(BORDER_CLASS);
  input.setAttribute('value', selectedElement.textContent);
}


function addEventListeners() {
  const elements = [
    'title',
  ]
  for (let element of elements) {
    console.log('element ' + element);
    const initialVersionElement = document.getElementById('initial-version-' + element);
    console.log('initialVersionElement ' + initialVersionElement);
    const aiVersionElement = document.getElementById('ai-version-' + element);
    console.log('aiVersionElement ' + aiVersionElement);
    const input = document.getElementById('id_' + element);
    initialVersionElement.addEventListener('click', () => {
      togglePairInput(initialVersionElement, aiVersionElement, input);
    });
    aiVersionElement.addEventListener('click', () => {
      console.log("aiVersionElement ==> click");
      togglePairInput(aiVersionElement, initialVersionElement, input);
    })
  }
}

addEventListeners();
