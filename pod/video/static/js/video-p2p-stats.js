/**
 * Show the p2p stats.
 */
function updateStats() {
    let httpMb = downloadTotals.http / 1048576;
    let p2pMb = downloadTotals.p2p / 1048576;
    let totalMb = httpMb + p2pMb;
    let uploadMb = uploadTotal / 1048576;
    let statInfo = "";
    if (totalMb != 0) {
        statInfo += '<i class="bi bi-person-fill-down" aria-hidden="true"></i> '
            + Number(totalMb).toFixed(1) + " MiB ";
        statInfo += '[ <i class="bi bi-server" aria-hidden="true"></i> : '
            + Number(httpMb).toFixed(1) + " MiB / "
            + Number((httpMb * 100) / totalMb).toFixed(0) + "%";
        statInfo +=  ' - <i class="bi bi-people" aria-hidden="true"></i> : '
            + Number(p2pMb).toFixed(1) + " MiB / "
            + Number((p2pMb * 100) / totalMb).toFixed(0) + "% ]";
        statInfo +=  ' - <i class="bi bi-person-fill-up" aria-hidden="true"></i> '
            + Number(uploadMb).toFixed(1) + " MiB";
    }
    var stat_info = document.querySelector("#p2p-stat-info");
    if(stat_info) {
        stat_info.innerHTML = statInfo;
    }
}
/**
 * Show the number of peers sharing file with the user.
 */
function updatePeers() {
    let statPeer = '<i class="bi bi-people-fill" aria-hidden="true"></i> ' + nb_peers;
    document.querySelector("#p2p-stat-peers").innerHTML = statPeer;
}
/**
 * Saves the bytes just download by the player by the download method.
 * This method is called by the bytes download event.
 *
 * @param {string} method method used to download bytes : http or p2p.
 * @param {string} segment current segment of video downloaded.
 * @param {number} bytes umber of bytes downloaded.
 */
function onBytesDownloaded(method, segment, bytes) {
    // console.log("onBytesDownloaded", method, size)
    downloadTotals[method] += bytes;
    updateStats();
}
/**
 * Saves the bytes just upload by the player.
 * This method is called by the bytes upload event.
 *
 * @param {string} method method used to upload bytes : only p2p.
 * @param {string} segment current segment of video uploaded.
 * @param {number} bytes umber of bytes uploaded.
 */
function onBytesUploaded(method, segment, bytes) {
    // console.log("onBytesUploaded", method, size)
    uploadTotal += bytes;
    updateStats();
}
/**
 * Increments the number of peer connected.
 * This method is called by the peer connect event.
 *
 * @param {object} peer the current peer connected.
 */
function onPeerConnect(peer) {
    nb_peers += 1;
    // console.log("peer_connect", peer.id, peer.remoteAddress);
    updatePeers()
}
/**
 * Decrements the number of connected peers.
 * This method is called by the peer close event.
 *
 * @param {number} peerId the id of the peer who are no more available.
 */
function onPeerClose(peerId) {
    nb_peers -= 1;
    // console.log("peer_close", peerId);
    updatePeers();
}