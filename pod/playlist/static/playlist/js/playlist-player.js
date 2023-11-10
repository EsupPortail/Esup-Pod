/**
 * @file Esup-Pod functions for the playlist player.
 * @since 3.5.0
 */

/**
 * This variable is `true` if the enrichment is active for the current page.
 */
var enrichmentIsOn = false;

/**
 * Link for the stylesheet for the enrichment application.
 */
var linkForStyleSheetForEnrichment;

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
    selectedElement.querySelector("span.rank").innerHTML = selectedElement.id;
    playerElements[currentIndex + 1].querySelector("span.rank").innerHTML = '<i class="bi bi-caret-right-fill" aria-hidden="true"></i>';
    let nextElement = playerElements[currentIndex + 1];
    if (!(nextElement.classList.contains('disabled'))) {
        const videoSrc = playerElements[currentIndex + 1].getAttribute('href');
        (currentIndex === -1) ? currentIndex = playerElements.length - 1 : "";
        if (nextElement.getAttribute('data-chapter') || playerElements[currentIndex].getAttribute('data-chapter')) {
            window.location.href = videoSrc;
        }
        else {
            const videoSrc = nextElement.getAttribute('data-url-for-video');
            const xhr = new XMLHttpRequest();
            xhr.open('GET', videoSrc);
            xhr.onreadystatechange = function () {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        delete player;
                        delete seektime;
                        delete options;
                        const responseData = JSON.parse(xhr.responseText);
                        const parser = new DOMParser();
                        const opengraphHtml = parser.parseFromString(responseData.opengraph, 'text/html');
                        const breadcrumbs = parser.parseFromString(responseData.breadcrumbs, 'text/html');
                        const pageAside = parser.parseFromString(responseData.page_aside, 'text/html');
                        const pageContent = parser.parseFromString(responseData.page_content, 'text/html');
                        const moreScript = parser.parseFromString(responseData.more_script, 'text/html');
                        const pageTitle = parser.parseFromString(responseData.page_title, 'text/html');
                        enrichmentIsOn = responseData.enrichment_is_on;
                        document.getElementById("video-player").innerHTML = '';
                        const tmp = document.querySelector('head');
                        const coupleOfElements = [
                            ['meta', 'property', 'head'],
                            ['meta', 'name', 'head'],
                        ]
                        for (let coupleOfElement of coupleOfElements) {
                            const metaTags = opengraphHtml.querySelectorAll(`${coupleOfElement[0]}[${coupleOfElement[1]}]`);
                            metaTags.forEach(metaTag => {
                                const elementToRefresh = document.querySelector(`${coupleOfElement[0]}[${coupleOfElement[1]}="${metaTag.getAttribute(coupleOfElement[1])}"]`);
                                if (elementToRefresh) {
                                    document.querySelector(`${coupleOfElement[0]}[${coupleOfElement[1]}="${metaTag.getAttribute(coupleOfElement[1])}"]`).setAttribute('content', metaTag.getAttribute('content'));
                                } else {
                                    document.querySelector(coupleOfElement[2]).appendChild(metaTag);
                                }
                            });
                        }
                        refreshElementWithDocumentFragment('#mainbreadcrumb', breadcrumbs);
                        const idElements = [
                            'card-manage-video',
                            'card-takenote',
                            'card-share',
                            'card-disciplines',
                            'card-types',
                        ]
                        for (let id of idElements) {
                            if (document.getElementById(id)) refreshElementWithDocumentFragment(`#${id}`, pageAside);
                        }
                        document.getElementById('card-enrichment-informations').style.display = enrichmentIsOn ? 'flex' : 'none';
                        refreshElementWithDocumentFragment('#video-player', pageContent);
                        refreshElementWithDocumentFragment('#more-script', moreScript);
                        refreshElementWithDocumentFragment('title', pageTitle);
                        document.querySelectorAll('script').forEach((item) => {
                            if (item.id == 'id_video_script') (0, eval)(item.innerHTML);
                            if (item.id == 'id_video_enrichment_script') (0, eval)(item.innerHTML);
                        });
                        let styleElementForEnrichment = document.getElementById('enrichment_style_id');
                        if (enrichmentIsOn) {
                            if (!styleElementForEnrichment) {
                                let styleElementForEnrichment = document.createElement('link');
                                styleElementForEnrichment.rel = 'stylesheet';
                                styleElementForEnrichment.type = 'text/css';
                                styleElementForEnrichment.href = linkForStyleSheetForEnrichment;
                                styleElementForEnrichment.id = 'enrichment_style_id';
                                document.head.appendChild(styleElementForEnrichment);
                            }
                        } else {
                            if (styleElementForEnrichment) {
                                styleElementForEnrichment.remove();
                            }
                        }
                    } else {
                        showalert(`Request error: ${xhr.statusText}`, 'alert-danger');
                    }
                }
            };
            xhr.send();
            updateUrl(nextElement.getAttribute('href'));
        }
    } else {
        switchToNextVideo();
    }
    scrollToSelectedVideo();
}


/**
 * Update the URL without refresh the page.
 *
 * @param {string} newUrl The new URL.
 */
function updateUrl(newUrl) {
    history.pushState({}, document.title, newUrl);
}


/**
 * Refresh element with the DocumentFragment.
 *
 * @param {string} elementQuerySelector The query selector for the element.
 * @param {*} html The html code.
 */
function refreshElementWithDocumentFragment(elementQuerySelector, newHTMLContent) {
    const fragment = document.createDocumentFragment();
    const newElement = newHTMLContent.querySelector(elementQuerySelector);
    fragment.appendChild(newElement.cloneNode(true));
    const elementToRefresh = document.querySelector(elementQuerySelector);
    elementToRefresh.innerHTML = '';
    elementToRefresh.innerHTML = fragment.querySelector(elementQuerySelector).innerHTML;
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


if (typeof videos === undefined) {
    let videos = document.querySelectorAll('.player-element');
} else {
    videos = document.querySelectorAll('.player-element');
}
videos.forEach(function (video) {
    new MutationObserver(scrollToSelectedVideo).observe(video, { attributes: true, attributeFilter: ['class'] });
});

document.addEventListener('DOMContentLoaded', function () {
    setTimeout(function () {
        scrollToSelectedVideo();
    }, 500);
});

var countdownElement = document.getElementById('pod-video-countdown');
