const exchangedValues = [];

addEventForReorganizedButton();

function addEventForReorganizedButton() {
    document.getElementById('reorganize-button').addEventListener('click', function (event) {
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
            console.log(convert2DTableToJson(exchangedValues));
            document.getElementById('json-data').value = convert2DTableToJson(exchangedValues);
        }
    });
}

function onDragStart(event) {
    event.dataTransfer.clearData();
    event.dataTransfer.setData('text/plain', event.target.id); // TODO Mettre "text" à la place de "text/plain" pour IE 9 à 11
    event.currentTarget.style.backgroundColor = "yellow";
}

function onDragOver(event) {
    event.preventDefault();
}

function onDrop(event) {
    event.preventDefault();
    const id = event.dataTransfer.getData('text');
    const draggableElement = document.getElementById(id);
    const dropzone = event.target;
    const child1 = draggableElement.children[0];
    const child2 = dropzone.children[0];
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
 * Activate the drap and drop in the page
 */
function activateDragAndDrop(parent) {
    const draggableElements = document.querySelectorAll('.draggable-container');
    const cardFooterElements = document.querySelectorAll('.card-footer');
    const sortForm = document.getElementById('sortForm')
    draggableElements.forEach(draggableElement => {
        draggableElement.setAttribute('draggable', true);
        draggableElement.addEventListener('dragstart', onDragStart);
        draggableElement.addEventListener('dragover', onDragOver);
        draggableElement.addEventListener('drop', onDrop);
        draggableElement.classList.add('shake-effect');
        draggableElement.children[0].classList.add('no-click');
    });
    cardFooterElements.forEach(cardFooterElement => {
        //cardFooterElement.style.visibility = 'hidden';
        cardFooterElement.style.opacity = '0';
        cardFooterElement.style.transition = 'opacity 0.9s ease';
    });
    sortForm.classList.add('no-click')
    sortForm.style.opacity = '0';
    sortForm.style.transition = 'opacity 0.9s ease';
    document.getElementById('cancel_btn_favorites_list').style.visibility = 'visible';
}

function convert2DTableToJson(table) {
    const jsonObject = {};
    for (let i = 0; i < table.length; i++) {
        jsonObject[i] = table[i];
    }
    return JSON.stringify(jsonObject);
}