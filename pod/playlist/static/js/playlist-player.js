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
        } else {
            switchToNextVideo();
        }
    }
}

/**
 * Scroll to the selected video.
 */
function scrollToSelectedVideo() {
    const selectedVideo = document.querySelector('.selected');
    if (selectedVideo) {
        selectedVideo.scrollIntoView({ behavior: 'smooth' });
    }
}

/**
 * Get startCountDown() promise.
 *
 * @returns The promise.
 */
function asyncStartCountDown() {
    return new Promise(function(resolve) {
        startCountdown(resolve);
    });
}

/**
 * Start the count down.
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
videos.forEach(function(video) {
    new MutationObserver(scrollToSelectedVideo).observe(video, { attributes: true, attributeFilter: ['class'] });
});

document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function () {
        scrollToSelectedVideo();
    }, 500);
});

var countdownElement = document.getElementById('countdown');
