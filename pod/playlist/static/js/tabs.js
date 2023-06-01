const linkElements = document.querySelectorAll('.tabs-menu li');
const contentElements = document.querySelectorAll('.tab-content');
const toggle = (targetId) => {
    console.log(targetId);
    contentElements.forEach((contentElement) => {
        const targetElement = document.querySelector(`[data-target="${contentElement.id}"]`);
        if (contentElement.id == targetId) {
            contentElement.style.display = 'block';
            if (targetElement.id !== 'is-active') {
                targetElement.id = 'is-active';
            }
        } else {
            contentElement.style.display = 'none';
            if (targetElement.id === 'is-active') {
                targetElement.id = '';
            }
        }
    });
}
linkElements.forEach((linkElement) => {
    linkElement.addEventListener('click', () => {
        toggle(linkElement.dataset.target);
    });
    if (linkElement.id === 'is-active') {
        toggle(linkElement.dataset.target);
    }
});