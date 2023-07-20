/**
 * Switch to the next video when this exists.
 */
function switchToNextVideo() {
    const playerElements = Array.from(document.querySelectorAll('.player-element'));
    const selectedElement = document.querySelector('.selected');
    const currentIndex = playerElements.indexOf(selectedElement);
    if (currentIndex < playerElements.length - 1) {
        playerElements[currentIndex + 1].classList.add('selected');
        selectedElement.classList.remove('selected');
        if (!(playerElements[currentIndex + 1].classList.contains('disabled'))) {
            window.location.href = playerElements[currentIndex + 1].getAttribute('href');
            // refreshElementWithDocumentFragment('collapseAside', playerElements[currentIndex + 1].getAttribute('href'));
        } else {
            switchToNextVideo();
        }
    }
}


function createCustomElement(content) {
    const newElement = document.createElement("div");
    newElement.innerHTML = content.innerHTML;
    return newElement;
}


function refreshElementWithDocumentFragment(elementId, url) {
    fetch(url)
        .then(response => response.text())
        .then(newContent => {
            const parser = new DOMParser();
            const newHTMLContent = parser.parseFromString(newContent, 'text/html');
            const fragment = document.createDocumentFragment();
            const newElement = createCustomElement(newHTMLContent.getElementById(elementId));
            fragment.appendChild(newElement);
            const elementToRefresh = document.getElementById(elementId);
            elementToRefresh.innerHTML = '';
            console.log(newElement);
            elementToRefresh.appendChild(newElement);
        });
}

/**
 * Scroll to the selected video.
 */
function scrollToSelectedVideo() {
    const scrollContainer = document.querySelector('.scroll-container');
    const selectedVideo = document.querySelector('.selected');
    if (selectedVideo && scrollContainer) {
        const containerRect = scrollContainer.getBoundingClientRect();
        const selectedRect = selectedVideo.getBoundingClientRect();
        const offsetTop = selectedRect.top - containerRect.top;
        scrollContainer.scrollTo({
            top: offsetTop,
            behavior: 'smooth'
        });
    }
}

/**
 * Get startCountDown() promise.
 *
 * @returns The promise.
 */
function asyncStartCountDown() {
    return new Promise(function (resolve) {
        startCountdown(resolve);
    });
}

/**
 * Start the count down.
 *
 * @param {function} callback The call back function.
 */
function startCountdown(callback) {
    countdownElement.textContent = count;
    if (count > 1) {
        count--;
        setTimeout(function () {
            startCountdown(callback);
        }, 1000);
    } else if (typeof callback === 'function') {
        callback();
    }
}

const videos = document.querySelectorAll('.player-element');
videos.forEach(function (video) {
    new MutationObserver(scrollToSelectedVideo).observe(video, { attributes: true, attributeFilter: ['class'] });
});

document.addEventListener('DOMContentLoaded', function () {
    setTimeout(function () {
        scrollToSelectedVideo();
    }, 500);
});

var countdownElement = document.getElementById('countdown');
