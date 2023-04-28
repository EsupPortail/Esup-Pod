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
    }
});

/**
 * Activate the drap and drop in the page
 */
function activateDragAndDrop() {
    // TODO A completer
}