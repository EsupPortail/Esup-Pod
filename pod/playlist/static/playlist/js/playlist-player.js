/**
 * Switch to the next video when this exists.
 */
function switchToNextVideo() {
    const playerElements = Array.from(document.querySelectorAll('.player-element'));
    const selectedElement = document.querySelector('.selected');
    let currentIndex = playerElements.indexOf(selectedElement);
    if (!(currentIndex < playerElements.length - 1)) {
        currentIndex = -1;
    }
    playerElements[currentIndex + 1].classList.add('selected');
    selectedElement.classList.remove('selected');
    let nextElement = playerElements[currentIndex + 1];
    if (!(nextElement.classList.contains('disabled'))) {
        const videoSrc = playerElements[currentIndex + 1].getAttribute('href');
        (currentIndex === -1) ? currentIndex = playerElements.length -1 : "";
        if (nextElement.getAttribute('data-chapter') || playerElements[currentIndex].getAttribute('data-chapter')) {
            window.location.href = videoSrc;
        }
        else {
            refreshElementWithDocumentFragment('#collapseAside', videoSrc);
            refreshElementWithDocumentFragment('#info-video', videoSrc);
            refreshElementWithDocumentFragment('title', videoSrc);
            refreshElementWithDocumentFragment('#chapter-for-playlist', videoSrc);
            let srcOptions = {
                src: nextElement.getAttribute('data-src'),
                type: nextElement.getAttribute('data-encoding-format'),
            };
            let player = videojs.getPlayer('podvideoplayer');
            player = videojs('podvideoplayer', options, function(){});
            player.setAttribute('data-vr', true);
            player.src(srcOptions);
            // TODO Replace the vtt thumbnails
            // checkVttThumbnails(player, nextElement);
            checkVr(player, nextElement);
            // checkChapters(player, nextElement);
            updateActiveBreadcrumb(nextElement);
            updateUrl(nextElement.getAttribute('href'));
            videojs('podvideoplayer').ready(function () {
                this.play();
            });
        }
    } else {
        switchToNextVideo();
    }
}


/**
 * Update the active element in the breadcrumb by the next video title.
 *
 * @param {*} nextElement The next element.
 */
function updateActiveBreadcrumb(nextElement) {
    const breadcrumbElement = document.querySelector('.breadcrumb-item.active');
    breadcrumbElement.textContent = nextElement.getElementsByClassName('title')[0].textContent;

}


/**
 * Update the URL without refresh the page.
 *
 * @param {string} newUrl The new URL.
 */
function updateUrl(newUrl) {
    history.pushState({}, document.title, newUrl);
}


function checkChapters(player, nextElement) {
    const chaptersExist = nextElement.getAttribute('data-chapter');
    if (chaptersExist) {
        const chaptersJSON = JSON.parse(chaptersExist).chapters;
        const chapterUlElement = document.createElement('ul');
        chapterUlElement.id = 'chapters';
        let contentUl = '';
        for (let chapterId = 0; chapterId < chaptersJSON.length; chapterId++) {
            console.log(chapterId);
            contentUl += `
                <li data-start="${chapterId + 1}"
                    data-id="${chapterId + 1}"
                    data-title="${chaptersJSON[chapterId].title}">
                    ${chaptersJSON[chapterId].title}
                </li>
            `;
            chapterUlElement.textContent = contentUl;
            console.log('chapterUlElement', chapterUlElement);
        }
        console.log('document.getElementById("podvideoplayer")', document.getElementById("podvideoplayer"));
        document.getElementById("podvideoplayer").content += `
            <div class="chapters-list inactive" role="menu">
                <h6><span class="vjs-icon-chapters"></span>${gettext('Chapters')}</h6>
                <ol id="chapters-list"></ol>
            </div>
        `;
        document.getElementById("podvideoplayer").textContent += chapterUlElement.textContent;
        console.log(JSON.parse(chaptersExist).chapters);

        const chaptersData = [
            { id: 1, title: "Chapter 1", start: 0 },
            { id: 2, title: "Chapter 2", start: 5 },
            // ... autres chapitres
        ];
        player.videoJsChapters({ ui: true });
        player.createChapters(chapterUlElement.querySelectorAll("li"));
        document.querySelector('.vjs-big-play-button').style.zIndex = '2';
        document.querySelector('.vjs-control-bar').style.zIndex = '3';
    } else {
        alert('No chapter');
    }
}


/**
 * Check if the VTT thumbnails exists for the next element. In this case, replace it.
 *
 * @param {*} player The video player.
 * @param {*} nextElement The next element.
 */
function checkVttThumbnails(player, nextElement) {
    const vttThumbnailsSrc = nextElement.getAttribute('data-vtt-thumbnails-src');
    if (vttThumbnailsSrc) {
        player.vttThumbnails({src: vttThumbnailsSrc});
    }
}


/**
 * Check if the VR must be activate for the next element. In this case, activate it.
 *
 * @param {*} player The video player.
 * @param {*} nextElement The next element.
 */
function checkVr(player, nextElement) {
    if (nextElement.getAttribute('data-is-360') == 'True') {
        player.usingPlugin('vr');
        player.vr({projection: '360'});
    } else {
        player.vr().dispose();
    }
}


// function loadNewPage(url) {
//     // Fais une requête pour récupérer le contenu de la nouvelle page
//     fetch(url)
//       .then(response => response.text())
//       .then(nouveauContenu => {
//         const tempElement = document.createElement("div");
//         tempElement.innerHTML = nouveauContenu;

//         // Exécute les scripts chargés sur la nouvelle page
//         const scripts = document.querySelectorAll("script");
//         scripts.forEach(script => {
//           const nouveauScript = document.createElement("script");
//           nouveauScript.textContent = script.textContent;
//           script.parentNode.replaceChild(nouveauScript, script);
//         });

//         // Remplace le contenu de la page actuelle par le nouveau contenu
//         document.documentElement.innerHTML = tempElement.innerHTML;
//       })
//       .catch(error => {
//         console.error("Erreur lors du chargement de la nouvelle page :", error);
//       });
//   }


function createCustomElement(content) {
    console.log(content);
    return content;
}


function refreshElementWithDocumentFragment(elementQuerySelector, url) {
    fetch(url)
        .then(response => response.text())
        .then(newContent => {
            const parser = new DOMParser();
            const newHTMLContent = parser.parseFromString(newContent, 'text/html');
            const fragment = document.createDocumentFragment();
            const newElement = newHTMLContent.querySelector(elementQuerySelector);
            fragment.appendChild(newElement.cloneNode(true));
            const elementToRefresh = document.querySelector(elementQuerySelector);
            elementToRefresh.innerHTML = '';
            console.log(fragment);
            elementToRefresh.innerHTML = fragment.querySelector(elementQuerySelector).innerHTML;
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
