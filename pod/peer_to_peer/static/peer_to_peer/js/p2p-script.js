console.log('P2P SCRIPT LOADED');

console.log('player', player);

let videoId = '47858-rabbit-and-others' // TODO Set the true identifier

let urlList = [];

let coreCache = [];

let peer; // TODO Update this ?

let firstTime = false;


function startConnect(options) {
    console.log('[p2p-script.js] startConnect()');
    let uuid = crypto.randomUUID();
    let peerId = `${videoId}_ID_${uuid}`;
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
        conn.on('data', function(data) {
            console.log(data);
        });
    });
}

/**
 * Get the peer identifiers.
 */
async function getIds() {
    console.log('[p2p-script.js] getIds()');
    let idList = [];
    let postData = {
        'url': videoId,
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
        console.log("RESPONSE JSON:", response.json());
        return response.json().then((data) => {
            alert(data);
            return data;
        });
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

player.on('xhr-hooks-ready', () => {
    console.log('[p2p-script.js] xhr-hooks-ready event');
    const playerOnResponseHook = (request, error, response) => {
        console.log('[p2p-script.js] Inside playerOnResponseHook');
        // console.log('[p2p-script.js] content_type:', content_type);
        console.log('[p2p-script.js] request: ', request);
        console.log('[p2p-script.js] response: ', response);
        // if (content_type.includes(response.headers['content-type'])) {
        console.log('[p2p-script.js] Condition met');
        urlList.push(`${response.url}_ID_${peer.id}`);
        coreCache[`${response.url}_ID_${peer.id}`] = response;
        if (urlList.length > 10) {
            delete coreCache[urlList[0]];
            urlList.splice(0, 1);
        }
        storeUrlsId();
        // }
    }

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
    player.tech().vhs.xhr = function(urlC, callback) {
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


startConnect({host:"127.0.0.1", port:"9000", path: '/', key: 'peerjs', debug:3});

