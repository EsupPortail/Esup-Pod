/**
 * URL to send a request to get the channel list.
 */
const GET_CHANNELS_REQUEST_URL = '/video/get-channels/';

/**
 * URL to send a request to get the channel tab list.
 */
const GET_CHANNEL_TAGS_REQUEST_URL = '/video/get-channel-tabs/';

/**
 * Number of channels to load per batch.
 */
const CHANNELS_PER_BATCH = 10;



/**
 * Get the channel list thanks to the AJAX request.
 *
 * @returns The AJAX request promise.
 */
function getChannelsAjaxRequest(page) {
    const url = `${GET_CHANNELS_REQUEST_URL}?page=${page}`;
    return new Promise(function(resolve, reject) {
        let xhr = new XMLHttpRequest();
        xhr.open('GET', url, true);
        xhr.onreadystatechange = function () {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    resolve(JSON.parse(xhr.responseText));
                } else {
                    reject(new Error('Request failed with status ' + xhr.status));
                }
            }
        }
        xhr.send();
    });
}



/**
 * Get the channel tab list thanks to the AJAX request.
 *
 * @param {boolean} nameOnly If this options is `true`, the channel tab list contains the name of tab only.
 *
 * @returns The AJAX request promise.
 */
function getChannelTabsAjaxRequest(nameOnly) {
    let url = GET_CHANNEL_TAGS_REQUEST_URL;
    if (nameOnly) {
        url = String.prototype.concat(url, '?only-name=true');
    }
    return new Promise(function(resolve, reject) {
        let xhr = new XMLHttpRequest();
        xhr.open('GET', url, true);
        xhr.onreadystatechange = function () {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    resolve(JSON.parse(xhr.responseText));
                } else {
                    reject(new Error('Request failed with status ' + xhr.status));
                }
            }
        }
        xhr.send();
    });
}



/**
 * Set the modal title when the user ask to view this modal.
 *
 * @param {HTMLElement} modalContentElement The HTML element of the modal.
 * @param {Array} channelsArray The channel list.
 */
function setModalTitle(modalContentElement, channelsCount) {
    const modalTitleElement = modalContentElement.querySelector('.modal-title');
    if (channelsCount > 1) {
        modalTitleElement.innerHTML = `<i class="bi bi-play-btn"></i>&nbsp; ${channelsCount} ${gettext('Channels')}`;
    } else {
        modalTitleElement.innerHTML = `<i class="bi bi-play-btn"></i>&nbsp; ${channelsCount} ${gettext('Channel')}`;
    }
}



/**
 * Convert a channel list to HTML modal list.
 *
 * @param {Array} channelsArray The channel list.
 *
 * @returns The HTML modal list.
 */
function convertToModalList(channelsArray) {
    const channelListGroupElement = document.createElement('ul');
    if (channelsArray.length > 0) {
        channelListGroupElement.classList.add('clist-group', 'list-group-flush', 'p-0');
        channelListGroupElement.id = 'list-channels';
        channelsArray.forEach(channel => {
            channelListGroupElement.appendChild(convertToModalListElement(channel));
        });
    } else {
        const channelListElement = document.createElement('li');
        channelListElement.classList.add('list-group-item', 'list-group-item-action');
        channelListElement.textContent = gettext('No channels found');
        channelListGroupElement.appendChild(channelListElement);
    }
    return channelListGroupElement;
}



/**
 * Convert a channel to a HTML modal list element.
 *
 * @param {any} channel The channel to convert.
 *
 * @returns The HTML modal list element.
 */
function convertToModalListElement(channel) {
    const channelListElement = document.createElement('li');
    channelListElement.classList.add('list-group-item', 'list-group-item-action');
    channelListElement.setAttribute('data-id', channel.id);
    const dFlexDivElement = document.createElement('div');
    dFlexDivElement.classList.add('d-flex', 'justify-content-between', 'align-items-center');
    const dFlexSpanElement = document.createElement('span');
    dFlexSpanElement.classList.add('d-flex', 'align-items-center', 'title-chaine');
    setImageForModal(dFlexSpanElement, channel);
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', channel.url);
    linkElement.id = `channel-title_${channel.id}`;
    linkElement.textContent = channel.title;
    const noWrapSpanElement = document.createElement('span');
    noWrapSpanElement.classList.add('text-nowrap');
    if (channel.themes.length > 0) {
        setChannelThemesForModal(noWrapSpanElement ,channel);
    }
    if (channel.videoCount > 1) {
        noWrapSpanElement.innerHTML += `<span class="badge text-bg-primary rounded-pill">${channel.videoCount} ${gettext('videos')}</span>`;
    } else {
        noWrapSpanElement.innerHTML += `<span class="badge text-bg-primary rounded-pill">${channel.videoCount} ${gettext('video')}</span>`;
    }
    const childAndParentCouples = [
        [dFlexSpanElement, linkElement],
        [dFlexDivElement, dFlexSpanElement],
        [dFlexDivElement, noWrapSpanElement],
        [channelListElement, dFlexDivElement],
    ]
    childAndParentCouples.forEach(childAndParentCouple => {
        childAndParentCouple[0].appendChild(childAndParentCouple[1]);
    });
    return channelListElement;
}



/**
 * Set the image in the innerHTML of span HTML element.
 *
 * @param {HTMLElement} dFlexSpanElement The span HTML element.
 * @param {any} channel The channel element.
 */
function setImageForModal(dFlexSpanElement, channel) {
    if (channel.headband) {
        dFlexSpanElement.innerHTML = `<img src="${channel.headbandImage}" width="20" class="rounded" alt="" loading="lazy">`;
    } else {
        dFlexSpanElement.innerHTML = '<i class="bi bi-play-btn pod-channel__item"></i>';
    }
}



/**
 * Append children to span HTML element. This children are channel theme element.
 *
 * @param {HTMLElement} spanElement The span HTML element.
 * @param {any} channel The channel.
 */
function setChannelThemesForModal(spanElement ,channel) {
    const channelThemes = channel.themes;
    channelThemes.forEach(channelTheme => {
        const themeSpanElement = document.createElement('a');
        themeSpanElement.classList.add('badge', 'btn-link', 'text-bg-primary', 'rounded-pill');
        themeSpanElement.style.marginRight = '1em';
        themeSpanElement.textContent = channelTheme.title;
        themeSpanElement.setAttribute('href', channelTheme.url);
        spanElement.appendChild(themeSpanElement);
    });
}



/**
 * Create modal for a specific channel tab.
 *
 * @param {any} channelTab The specific channel tab.
 */
function createModalFor(channelTab) {
    const headerElement = document.getElementsByTagName('header')[0];
    const modalElement = document.createElement('div');
    modalElement.classList.add('modal', 'fade', `chaines-modal-${channelTab.id}`);
    const attributeCouples = [
        ['tabindex', '-1'],
        ['role', 'dialog'],
        ['aria-hidden', 'true'],
    ]
    attributeCouples.forEach(attributeCouple => {
        modalElement.setAttribute(attributeCouple[0], attributeCouple[1]);
    });
    modalElement.innerHTML = `
        <div class="modal-dialog modal-lg modal-pod-full">
            <div class="modal-content">
                <div class="modal-header">
                    <h2 class="modal-title">
                        <i class="bi bi-play-btn"></i>&nbsp;
                        <span class="spinner-border text-primary" role="status">
                        </span>
                    </h2>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="${gettext('Close')}"></button>
                </div>
            <div class="modal-body">
                <div class="text-center">
                    <span class="spinner-border text-primary" role="status">
                    </span>
            </div>
            </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">${gettext('Close')}</button>
                </div>
            </div>
        </div>
    `;
    headerElement.appendChild(modalElement);
    modalElement.addEventListener('shown.bs.modal', function () {
        const modalContentElement = this.querySelector('.modal-content');
        getChannelTabsAjaxRequest()
            .then(function (channelTabs) {
                let channelsArray = Object.values(channelTabs[channelTab.id].channels);
                setModalTitle(modalContentElement, channelsArray.length);
                modalContentElement.querySelector('.modal-body').innerHTML = convertToModalList(channelsArray).innerHTML;
                console.log(modalContentElement);
            })
            .catch(function (error) {
                console.error(error);
            });
    });
}



const channelModal = document.querySelector('.chaines-modal');
let allChannelsLoaded = false;
channelModal.addEventListener('shown.bs.modal', function () {
    const modalContentElement = this.querySelector('.modal-content');
    let currentPage = 1;

    function loadNextBatchOfChannels() {
        getChannelsAjaxRequest(currentPage)
            .then(function (channels) {
            let channelsArray = Object.values(channels['channels']);
            if (currentPage <= channels['totalPages']) {
                channelsArray.forEach(channel => {
                    modalContentElement.querySelector('.clist-group').appendChild(convertToModalListElement(channel));
                });
                currentPage++;
                loadNextBatchOfChannels();
            } else {
                allChannelsLoaded = true;
            }
            })
            .catch(function (error) {
                console.error(error);
            });
    }


    console.log(allChannelsLoaded);
    if (allChannelsLoaded === false) {
        getChannelsAjaxRequest()
            .then(function (channels) {
                let channelsArray = Object.values(channels['channels']);
                setModalTitle(modalContentElement, channels['count']);
                modalContentElement.querySelector('.modal-body').appendChild(convertToModalList(channelsArray));
                modalContentElement.querySelector('.modal-body').querySelector('.text-center').remove();
                if (channels['count'] > CHANNELS_PER_BATCH) {
                    currentPage++;
                    loadNextBatchOfChannels();
                }
                console.log(modalContentElement);
                console.log(channels);
            })
            .catch(function (error) {
                console.error(error);
            });
    }
});

const burgerMenu = document.getElementById('pod-navbar__menu');
burgerMenu.addEventListener('shown.bs.offcanvas', function () {
    const navChannelTabs = document.getElementById('tab-list');
    getChannelTabsAjaxRequest(true)
    .then(function (channelTabs) {
        let channelTabsArray = Object.values(channelTabs);
        burgerMenu.querySelector('.progress').remove();
        console.log(channelTabs);
        channelTabsArray.forEach(channelTab => {
            const navChannelTab = document.createElement('li');
            const buttonChannelTab = document.createElement('button');
            navChannelTab.classList.add('nav-item');
            buttonChannelTab.classList.add('nav-link');
            buttonChannelTab.setAttribute('data-bs-toggle', 'modal');
            buttonChannelTab.setAttribute('data-bs-target', `.chaines-modal-${channelTab.id}`);
            buttonChannelTab.innerHTML = `<i class="bi bi-play-btn pod-nav-link-icon"></i> ${channelTab.name}`;
            createModalFor(channelTab);
            navChannelTab.appendChild(buttonChannelTab);
            navChannelTabs.appendChild(navChannelTab);
        })
    })
    .catch(function (error) {
        console.error(error);
    });
});
