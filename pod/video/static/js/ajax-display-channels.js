/**
 * URL to send a request to get the channel list.
 */
const GET_CHANNELS_REQUEST_URL = '/video/get-channels/';

/**
 * URL to send a request to get the channel tab list.
 */
const GET_CHANNEL_TAGS_REQUEST_URL = '/video/get-channel-tabs/';



/**
 * Get the channel list thanks to the AJAX request.
 *
 * @returns The AJAX request promise.
 */
function getChannelsAjaxRequest() {
    return new Promise(function(resolve, reject) {
        let xhr = new XMLHttpRequest();
        xhr.open('GET', GET_CHANNELS_REQUEST_URL, true);
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


// getChannelsAjaxRequest()
//     .then(function (channels) {
//         console.log(channels);
//     })
//     .catch(function (error) {
//         console.error(error);
//     });


// getChannelTabsAjaxRequest()
//     .then(function (channelTabs) {
//         console.log(channelTabs);
//     })
//     .catch(function (error) {
//         console.error(error);
//     });


// getChannelTabsAjaxRequest(true)
//     .then(function (channelTabs) {
//         console.log(channelTabs);
//     })
//     .catch(function (error) {
//         console.error(error);
//     });
