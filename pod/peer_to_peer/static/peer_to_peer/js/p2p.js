class P2p {

    /**
     * Video identifier for the current session.
     *
     * @type {string}
     *
     * @default undefined
     */
    videoSlug;



    /**
     * List of URLs related to the video.
     *
     * @type {Array}
     *
     * @default []
     */
    urlList = [];



    /**
     * Peer object for peer-to-peer communication.
     *
     * @type {Peer}
     *
     * @default undefined // TODO Update this ?
     */
    peer;



    /**
     * Flag indicating whether it's the first time performing an action.
     *
     * @type {boolean}
     *
     * @default false
     */
    firstTime = false;



    constructor(videoSlug) {
        this.videoSlug = videoSlug;
    }



    /**
     * Retrieves peer identifiers associated with the current video.
     * @async
     * @returns {Array} - A list of peer identifiers.
     */
    async getIds() {
        let idList = [];
        let postData = {
            'url': this.videoSlug,
        };
        await fetch('http://localhost:9090/peer-to-peer/get-ids/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(postData),
        }).then(response => response.json())
            .then(response => {
                idList = [].concat(response);
            })
            .catch(err => console.error(err));
        return idList;
    }



    // TODO Add the other functions
}