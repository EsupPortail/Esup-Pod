var translationDone = false;

document.getElementById('podvideoplayer_html5_api').addEventListener('play', function () {
    if (!translationDone) {
        const elementToTranslateList = [
            ['.skip-back', 'Revenir de 10 secondes en arrière'],
            ['.skip-forward', 'Aller de 10 seconds en avant'],
        ]
        for (let elementToTranslate of elementToTranslateList) {
            translateTitleOfVideoPlayerButton(elementToTranslate[0], elementToTranslate[1]);
        }
    }
});


/**
 * Translate the title of the video player button.
 *
 * @param {string} querySelectorButton The query selector for the button.
 * @param {string} title The title.
 */
function translateTitleOfVideoPlayerButton(querySelectorButton, title) {
    const translatedTitle = gettext(title);
    const videoPlayerButton = document.querySelector(querySelectorButton);
    if (videoPlayerButton) {
        const videoPlayerSpan = videoPlayerButton.querySelector('.vjs-control-text');
        videoPlayerButton.title = translatedTitle;
        videoPlayerSpan.textContent = translatedTitle;
    }
}

// 'Seek back 10 seconds'