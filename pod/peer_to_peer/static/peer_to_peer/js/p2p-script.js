console.log('P2P SCRIPT LOADED');

console.log('player', player);

/**
 * Video identifier for the current session.
 * @type {string}
 * @default string // TODO Set true ID
 */
let videoSlug = '47858-rabbit-and-others';

/**
 * List of URLs related to the video.
 * @type {Array}
 * @default []
 */
let urlList = [];

/**
 * Cache for storing core data associated with URLs.
 * @type {Object}
 * @default {}
 */
let coreCache = [];

/**
 * Peer object for peer-to-peer communication.
 * @type {Peer}
 * @default undefined // TODO Update this ?
 */
let peer;

/**
 * Flag indicating whether it's the first time performing an action.
 * @type {boolean}
 * @default false
 */
let firstTime = false;

/**
 * Establishes a peer-to-peer connection using the provided options.
 * @param {Object} options - Configuration options for the Peer object.
 * @returns {void}
 */
function startConnect(options) {
    console.log('[p2p-script.js] startConnect()');
    let uuid = crypto.randomUUID();
    let peerId = `${videoSlug}_ID_${uuid}`;
    peer = new Peer(peerId, options);
    console.log("Peer:", peer);

    if (false) { // TODO Delete this test | Set true for sender
        let idToConnect = '47858-rabbit-and-others-100bd4a6-9077-440f-8cb3-21e25a096881';
        let conn = peer.connect(idToConnect);
        conn.on('open', function () {
            conn.send('Hi!');
        });
    }

    peer.on('connection', function (conn) {
        console.log('CONNECTION');
        conn.on('data', function (data) {
            console.log(data);
        });
    });
}

/**
 * Retrieves peer identifiers associated with the current video.
 * @async
 * @returns {Array} - A list of peer identifiers.
 */
async function getIds() {
    console.log('[p2p-script.js] getIds()');
    let idList = [];
    let postData = {
        'url': videoSlug,
    };
    console.log('[p2p-script.js] postData:', postData);
    // TODO Update the URL
    await fetch('http://localhost:9090/peer-to-peer/get-ids/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(postData),
    }).then(response => response.json())
        .then(response => {
            idList = [].concat(response);
            console.log(idList);
        })
        .catch(err => console.error(err));
    return idList;
}

/**
 * Stores URLs associated with the current peer's ID on the server.
 * @async
 * @returns {void}
 */
async function storeUrlsId() {
    console.log('[p2p-script.js] storeUrlsId()');
    let fetch_status;
    let postData = {};
    for (let i = 0; i < urlList.length; i++) {
        postData[urlList[i]] = 1;
    }
    console.log('[p2p-script.js] postData:', postData);
    console.log('[p2p-script.js] JSON.stringify(postData):', JSON.stringify(postData));
    // TODO Change the URL.
    fetch(`http://localhost:9090/peer-to-peer/store/${peer.id}/`, {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            // TODO Add CSRF cookie
        },
        body: JSON.stringify(postData),
    }).then(function (response) {
        fetch_status = response.status;
        console.log("JSON", response);
        return response.json();
    }).then(function (json) {
        console.log("FETCH-STATUS:", fetch_status);
        if (fetch_status == 200) {
            console.log(json);
        }
    }).catch(function (error) {
        console.log(error);
    });
}

// TODO Call the function

/**
 * Sets up event hooks and overrides XHR behavior when the 'xhr-hooks-ready' event is triggered on the video player.
 * @listens player#xhr-hooks-ready
 * @returns {void}
 */
player.on('xhr-hooks-ready', () => {
    console.log('[p2p-script.js] xhr-hooks-ready event');

    /**
     * Handles the response hook for XHR requests.
     * @param {Object} request - The XHR request object.
     * @param {Object} error - The XHR error object.
     * @param {Object} response - The XHR response object.
     */
    const playerOnResponseHook = (request, error, response) => {
        console.log('[p2p-script.js] Inside playerOnResponseHook');
        // console.log('[p2p-script.js] content_type:', content_type);
        console.log('[p2p-script.js] request: ', request);
        console.log('[p2p-script.js] response: ', response);
        // if (content_type.includes(response.headers['content-type'])) {
        console.log('[p2p-script.js] Condition met');
        urlList.push(peer.id);
        coreCache[`${response.url}_ID_${peer.id}`] = response;
        if (urlList.length > 10) {
            delete coreCache[urlList[0]];
            urlList.splice(0, 1);
        }
        storeUrlsId();
        // }
    }

    /**
     * Handles the request hook for XHR requests.
     * @param {Object} options - The XHR options object.
     * @returns {Object} - Modified XHR options object.
     */
    const playerOnRequestHook = (options) => {
        let headers = options['headers'];
        if (headers && headers['Range']) {
            let add = "?";
            if (options.uri.indexOf('?') > -1) add = '&';
            options.uri = options.uri + add + headers['Range']
        }
        return options;
    }

    console.log('[p2p-script.js] player.tech().vhs.xhr:', player.tech().vhs.xhr);

    /**
     * Overrides the XHR behavior on the video player.
     * @param {string|Object} urlC - The URL or XHR options.
     * @param {Function} callback - The XHR callback function.
     * @returns {Object} - XHR result.
     */
    player.tech().vhs.xhr = function (urlC, callback) {
        console.log("URLC CALLLLLLLL", urlC, callback);
        let url = '';
        console.log('[p2p-script.js] player.tech().vhs.xhr');
        if (typeof urlC === 'object') {
            url = urlC.uri;
            console.log('[p2p-script.js] url:', url);
            console.log('[p2p-script.js] urlC:', urlC);
            console.log('[p2p-script.js] urlC.responseType:', urlC.responseType);
            if (urlC.responseType === 'arraybuffer') {
                firstTime = true;
                if (nbLog < 10) {
                    console.log('urlC', urlC);
                    nbLog++;
                }
                let ids = []; // TODO Go the search ID in the server
                if (ids.length > 0) {
                    console.log('youpi');
                }
                videojs.Vhs.xhr.onResponse(playerOnResponseHook);
                return videojs.Vhs.xhr(urlC, callback);
            } else if (!firstTime) {
                firstTime = true;
                url = urlC.url;
                videojs.Vhs.xhr.onResponse(playerOnResponseHook);
                return videojs.Vhs.xhr(urlC, callback);
            }
            // } else {
            //     url = urlC.url;
            //     videojs.Vhs.xhr.onResponse(playerOnResponseHook);
            //     return videojs.Vhs.xhr(urlC, callback);
            // }
        } else {
            url = urlC;
            videojs.Vhs.xhr.onResponse(playerOnResponseHook);
            return videojs.Vhs.xhr(urlC, callback);
        }
    };

    // FIN player.on('xhr-hooks-ready', () => {
});


startConnect({ host: "127.0.0.1", port: "9000", path: '/', key: 'peerjs', debug: 3 });
