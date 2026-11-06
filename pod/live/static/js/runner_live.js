/**
 * @file Esup-Pod playback polling for automatic Esup-Runner Live sessions.
 */
window.PodRunnerLive = {
  /**
   * Follow playback readiness and replace the source when the Live session changes.
   * @param {Object} player Video.js player receiving the ready HLS source.
   * @param {Object} callbacks Availability callbacks for the surrounding page.
   * @returns {Function} Function that stops polling and aborts the current request.
   */
  start(player, callbacks = {}) {
    const status = document.getElementById("runner-live-status");
    let currentURL = "";
    let currentSession = null;
    let timer;
    let controller;
    let disposed = false;
    let suspended = false;
    let playbackFailed = false;
    let lastDiagnostic = "";
    const messages = {
      waiting: status.dataset.waitingMessage,
      starting: status.dataset.startingMessage,
      hls_waiting: status.dataset.hlsWaitingMessage,
      ended: status.dataset.endedMessage,
      failed: status.dataset.failedMessage,
      unavailable: status.dataset.unavailableMessage,
      mixed_content: status.dataset.mixedContentMessage,
      playback_error: status.dataset.playbackErrorMessage,
      polling_error: status.dataset.pollingErrorMessage,
      autoplay: status.dataset.autoplayMessage,
    };

    /** Show a translated status and log controlled error codes without URLs. */
    const showStatus = (reason, details = {}, isError = false) => {
      const message = messages[reason] || messages.waiting;
      if (status.textContent !== message) status.textContent = message;
      status.dataset.diagnostic = reason;
      status.hidden = false;
      status.classList.toggle("alert-danger", isError);
      status.classList.toggle("alert-info", !isError);
      const diagnostic = JSON.stringify([reason, details]);
      if (isError && diagnostic !== lastDiagnostic) {
        console.warn("Esup-Pod Live playback", { reason, ...details });
      }
      lastDiagnostic = diagnostic;
    };

    /** Remove an unavailable HLS source and display its current diagnostic. */
    const clear = (reason = "waiting", details = {}, isError = false) => {
      if (currentURL || player.currentSrc()) {
        currentURL = "";
        currentSession = null;
        player.pause();
        player.reset();
      }
      showStatus(reason, details, isError);
      if (callbacks.onUnavailable) callbacks.onUnavailable();
    };

    /** Explain unready lifecycle states without confusing them with player errors. */
    const showUnavailable = (state) => {
      playbackFailed = false;
      const reasons = {
        pending: "starting", starting: "starting", running: "hls_waiting",
        stopping: "ended", completed: "ended", stopped: "ended",
        failed: "failed", unavailable: "unavailable", waiting_source: "waiting",
      };
      const reason = reasons[state] || "unavailable";
      clear(reason, {}, reason === "failed" || reason === "unavailable");
    };

    /** Keep the source for a later retry and expose only the safe media error code. */
    const onPlayerError = () => {
      if (disposed || !currentURL) return;
      const error = player.error();
      const code = Number.isInteger(error?.code) ? error.code : null;
      playbackFailed = true;
      showStatus("playback_error", { media_error_code: code }, true);
      if (callbacks.onUnavailable) callbacks.onUnavailable();
    };

    /** Clear a persistent playback warning only when media actually starts playing. */
    const onPlaying = () => {
      if (disposed || !currentURL) return;
      playbackFailed = false;
      lastDiagnostic = "";
      status.hidden = true;
      if (callbacks.onAvailable) callbacks.onAvailable();
    };

    /** Retry the assigned HLS source without needing the manager to recover. */
    const loadSource = () => {
      player.src({ src: currentURL, type: "application/x-mpegURL" });
      const source = currentURL;
      const playing = player.play();
      if (playing && playing.catch) playing.catch((error) => {
        if (disposed || currentURL !== source) return;
        if (error?.name === "NotAllowedError") showStatus("autoplay");
        else if (error?.name !== "AbortError") onPlayerError();
      });
    };

    /** Preserve actual media playback when discovery temporarily fails. */
    const keepPlayback = (reason, details = {}) => {
      if (currentURL && !playbackFailed) return;
      showStatus(reason, details, true);
      if (callbacks.onUnavailable) callbacks.onUnavailable();
      if (currentURL && playbackFailed) loadSource();
    };

    /** Load the exact ready HLS address while making mixed content errors visible. */
    const applyStream = (data) => {
      const mediaURL = new URL(data.hls_url);
      if (window.location.protocol === "https:" && mediaURL.protocol === "http:") {
        playbackFailed = false;
        clear("mixed_content", { page_scheme: "https", hls_scheme: "http" }, true);
        return;
      }
      if (currentURL !== data.hls_url || currentSession !== data.live_id || playbackFailed) {
        currentURL = data.hls_url;
        currentSession = data.live_id;
        if (!playbackFailed) status.hidden = true;
        loadSource();
      }
      if (callbacks.onAvailable) callbacks.onAvailable();
    };

    /** Refresh playback through Pod and schedule the next availability check. */
    const poll = async () => {
      if (disposed || suspended) return;
      let nextDelay = 5000;
      const requestController = new AbortController();
      controller = requestController;
      const isCurrent = () => !disposed && !suspended && controller === requestController;
      // Allow discovery and bounded master/media/segment probes to complete.
      const timeout = setTimeout(() => requestController.abort(), 30000);
      try {
        const response = await fetch(status.dataset.streamUrl, {
          credentials: "same-origin",
          cache: "no-store",
          signal: requestController.signal,
          headers: { Accept: "application/json" },
        });
        if (!isCurrent()) return;
        if (!response.ok || response.redirected) {
          const details = { http_status: response.status };
          if (response.redirected || (response.status < 500 && response.status !== 429)) {
            clear("polling_error", details, true);
          } else {
            nextDelay = 10000;
            keepPlayback("polling_error", details);
          }
          return;
        }
        const data = await response.json();
        if (!isCurrent()) return;
        const playable = data.state === "running" && data.hls_ready === true &&
          typeof data.hls_url === "string" && Boolean(data.hls_url);
        if (data.retryable === true && !["stopping", "completed", "failed", "stopped"].includes(data.state)) {
          nextDelay = 10000;
          if (playable) applyStream(data);
          else keepPlayback("polling_error");
        } else if (!playable) {
          showUnavailable(data.state);
        } else applyStream(data);
      } catch {
        nextDelay = 10000;
        if (isCurrent()) keepPlayback("polling_error", {
          failure: requestController.signal.aborted ? "timeout" : "network_or_response_error",
        });
      } finally {
        clearTimeout(timeout);
        if (isCurrent()) timer = setTimeout(poll, nextDelay);
      }
    };

    /** Cancel requests, timers and listeners when the player or page closes. */
    const stop = () => {
      if (disposed) return;
      disposed = true;
      clearTimeout(timer);
      if (controller) controller.abort();
      player.off("error", onPlayerError);
      player.off("playing", onPlaying);
      player.off("dispose", stop);
      window.removeEventListener("pagehide", onPageHide);
      window.removeEventListener("pageshow", onPageShow);
    };

    /** Suspend cached pages while keeping their player and restoration listeners. */
    const onPageHide = (event) => {
      if (!event.persisted) {
        stop();
        return;
      }
      suspended = true;
      clearTimeout(timer);
      if (controller) controller.abort();
    };

    /** Refresh availability immediately when browser history restores the page. */
    const onPageShow = (event) => {
      if (!event.persisted || disposed || !suspended) return;
      suspended = false;
      poll();
    };
    player.on("error", onPlayerError);
    player.on("playing", onPlaying);
    player.on("dispose", stop);
    window.addEventListener("pagehide", onPageHide);
    window.addEventListener("pageshow", onPageShow);
    poll();
    return stop;
  },
};
