const exchangedValues = [];
var infinite;

const reorganizeButtonsSpanElement = document.getElementById('reorganize-buttons');
const collapseAsideElement = document.getElementById('collapseAside');
const reorganizeButton = document.getElementById('reorganize-button');

addEventForReorganizedButton();

/**
 * Add or remove the CSS class to make drop zone hover.
 *
 * @param {string} state State of style (`add` or `remove`).
 * @param {Element} element Element to add CSS class.
 */
function addOrRemoveDropZoneHoverStyleClass(state, element) {
  const className = 'dropzone-hover';
  if (state === 'add') {
    element.classList.add(className);
  } else {
    element.classList.remove(className);
  }
}


/**
 * Add an event listener to the 'reorganize-button' element.
 */
function addEventForReorganizedButton() {
  if (reorganizeButton) {
    reorganizeButton
      .addEventListener('click', function (event) {
        const draggableElements = document.querySelectorAll('.draggable-container',);
        draggableElements.forEach((draggableElement) => {
          draggableElement.addEventListener('dragenter', (event) => {
            addOrRemoveDropZoneHoverStyleClass('add', event.target);
          });
          draggableElement.addEventListener('dragleave', (event) => {
            addOrRemoveDropZoneHoverStyleClass('remove', event.target);
          });
          draggableElement.addEventListener('drop', (event) => {
            addOrRemoveDropZoneHoverStyleClass('remove', event.target);
          });
        });
        if (this.id == 'reorganize-button') {
          event.preventDefault();
          activateDragAndDrop();
          this.id = 'save-button';
          this.title = gettext('Save your reorganization');
          const iconElement = this.querySelector('i');
          const spanElement = this.querySelector('span');
          iconElement.classList.replace('bi-arrows-move', 'bi-save');
          spanElement.textContent = gettext('Save');
        } else if (this.id == 'save-button') {
          document.getElementById('json-data').value =
            convert2DTableToJson(exchangedValues);
        }
      });
  }
}


/**
 * Clear and transfer data when drag event starts.
 *
 * @param {Event} event The name of the event.
 */
function onDragStart(event) {
  event.dataTransfer.clearData();
  event.dataTransfer.setData("text/plain", event.target.id);
  event.target.classList.toggle("shake-effect-active");
}


/**
 * Prevent the default behavior of the element during the event.
 *
 * @param {Event} event The name of the event.
 */
function onDragOver(event) {
  event.preventDefault();
  event.dataTransfer.dropEffect = 'move';
}


/**
 * Performs a swap between the dragged elements when dropping.
 *
 * @param {Event} event The name of the event.
 */
function onDrop(event) {
  event.preventDefault();
  const id = event.dataTransfer.getData('text');
  const draggableElement = document.getElementById(id);
  const dropzone = event.target;
  const child1 = draggableElement.children[0];
  const child2 = dropzone.children[0];
  draggableElement.classList.toggle('shake-effect-active');
  if (child1.id == child2.id) return;
  const child1copy = child1.cloneNode(true);
  const child2copy = child2.cloneNode(true);
  draggableElement.appendChild(child2copy);
  dropzone.appendChild(child1copy);
  child1.remove();
  child2.remove();
  exchangedValues.push([child1.id, child2.id]);
}


/**
 * Activate the drag and drop in the page
 */
function activateDragAndDrop(parent) {
  const draggableElements = document.querySelectorAll(".draggable-container");
  const cardFooterElements = document.querySelectorAll(".card-footer");
  draggableElements.forEach((draggableElement) => {
    draggableElement.setAttribute('draggable', true);
    draggableElement.addEventListener('dragstart', onDragStart);
    draggableElement.addEventListener('dragover', onDragOver);
    draggableElement.addEventListener('drop', onDrop);
    draggableElement.classList.add('shake-effect');
    draggableElement.children[0].classList.add('no-click');
  });
  updateCollapseAside();
  infinite.removeLoader();
  document
    .getElementById('cancel_btn_favorites_list')
    .classList.remove('d-none');
  if (document.getElementById('card-manage-playlist')) {
    document
      .getElementById('card-manage-playlist')
      .classList.add('d-none');
  }
}


/**
 * Convert a 2D table into a JSON string representation.
 *
 * @param {Array} table The 2D table to convert.
 *
 * @returns {String} The JSON string representation.
 */
function convert2DTableToJson(table) {
  const jsonObject = {};
  for (let i = 0; i < table.length; i++) {
    jsonObject[i] = table[i];
  }
  return JSON.stringify(jsonObject);
}


/**
 * Update collapse aside to help user.
 */
function updateCollapseAside() {
  const helpInformations = document.querySelector('#card-sharedraftversion');
  helpInformations.classList.remove('card-hidden');
}
