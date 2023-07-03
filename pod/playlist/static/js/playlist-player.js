const idList = [];
var idRun = 0;
const videoInformationsList = []

/**
 * Switch to an other video in the playlist. This function is called when the user click on the video in playlist player or when the last video is ended.
 *
 * @param {HTMLElement} buttonPlaylistElement The card of the video to display.
 * @param {{}} informations The informations of the video to display.
 */
function switchVideo(buttonPlaylistElement, informations) {
    mp4_sources = informations.get_video_mp4_json;
    var srcOptions = {
        src: informations.source_file_url,
        type: informations.encoding_format,
    };
    player.src(srcOptions);
    const url = buttonPlaylistElement.getAttribute("data-video-href");
    fetch(url, {
        method: 'GET',
    })
        .then((response) => {
            if (response.ok) {
                return response.text();
            } else {
                throw new Error('Network response was not ok.');
            }
        })
        .then((data) => {
            const parser = new DOMParser();
            const html = parser.parseFromString(data, 'text/html');
            const currentPageToRefreshElement = document.querySelector('.active');
            const elementToRefreshList = [
                document.getElementById('info-video'),
                document.getElementById('card-managevideo'),
                document.getElementById('card-takenote'),
                document.getElementById('card-share'),
                document.getElementById('card-share'),
                document.getElementById('card-types'),
                document.getElementById('card-tags'),
                document.getElementById('pod-first-content'),
                document.getElementById('id_video_script'),
            ];
            document.title = html.title;
            for (let elementToRefresh of elementToRefreshList) {
                if (elementToRefresh) {
                    elementToRefresh.replaceWith(html.getElementById(elementToRefresh.id));
                }
            }
            currentPageToRefreshElement.textContent = document.getElementById('info-video').querySelector('.page_title').textContent;
        })
        .catch(error => {
            console.log('ERROR: ', error);
        });
    const elements = document.querySelectorAll(".selected");
    for (let i = 0; i < elements.length; i++) {
        elements[i].classList.remove('selected');
    }
    buttonPlaylistElement.classList.add('selected');
    idRun = idList.indexOf(buttonPlaylistElement.id);
    player.play();
}

/**
 * Switch to the next video when this exists.
 */
function switchToNextVideo() {
    if (idRun < idList.length - 1) {
        switchVideo(
            document.getElementById(idList[idRun + 1]),
            videoInformationsList[idRun + 1],
        );
    }
}

/**
 * Add an EventListener to a video card. This function is called for all accessible card videos.
 *
 * @param {HTMLElement} buttonPlaylistElement The video card.
 * @param {{}} informations The video informations.
 */
function preventRefreshButtonPlaylist(buttonPlaylistElement, informations) {
    if (buttonPlaylistElement) {
        buttonPlaylistElement.addEventListener('click', (event) => {
            switchVideo(buttonPlaylistElement, informations);
        });
    }
}

function checkFirstVideoInGet() {
    const selectedElement = document.querySelectorAll(".selected")[0];
    console.log('selectedElement', selectedElement);
    console.log('idRun (last)', idRun);
    switchVideo(selectedElement, firstVideoInformations);
    console.log('idRun (now)', idRun);
}
