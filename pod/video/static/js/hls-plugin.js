// Thanks https://github.com/streamroot/videojs-hlsjs-plugin
// We duplicated this plugin to choose the hls.js version we want, because streamroot only provide a bundled file

import "/static/hls.js/dist/hls.js";
import "/static/video.js/dist/video.min.js";

let alreadyRegistered = false;

const registerSourceHandler = function(vjs) {
  console.log(Hls.isSupported());
  if (!Hls.isSupported()) {
    console.log("Hls.js is not supported in this browser.");
    return;
  }

  const html5 = vjs.getTech("Html5");

  if (!html5) {
    console.error('No "Html5" tech found in videojs');
    return
  }

  if (alreadyRegistered) return;

  alreadyRegistered = true;

  // FIXME: typings
  html5.registerSourceHandler(
    {
      canHandleSource: function(source) {
        const hlsTypeRE = /^application\/x-mpegURL|application\/vnd\.apple\.mpegurl$/i;
        const hlsExtRE = /\.m3u8/i;

        if (hlsTypeRE.test(source.type)) return "probably";
        if (hlsExtRE.test(source.src)) return "maybe";

        return "";
      },

      handleSource: function(source, tech) {
        if (tech.hlsProvider) {
          tech.hlsProvider.dispose();
        }

        tech.hlsProvider = new Html5Hlsjs(vjs, source, tech);

        return tech.hlsProvider;
      }
    },
    0
  )

  // FIXME: typings
  vjs.Html5Hlsjs = Html5Hlsjs;
}

// ---------------------------------------------------------------------------
// HLS options plugin
// ---------------------------------------------------------------------------

const Plugin = videojs.getPlugin("plugin")

class HLSJSConfigHandler extends Plugin {
  constructor(player, options) {
    super(player, options)

    if (!options) return;

    if (!player.srOptions_) {
      player.srOptions_ = {};
    }

    if (!player.srOptions_.hlsjsConfig) {
      player.srOptions_.hlsjsConfig = options.hlsjsConfig;
    }

    if (options.levelLabelHandler && !player.srOptions_.levelLabelHandler) {
      player.srOptions_.levelLabelHandler = options.levelLabelHandler;
    }

    registerSourceHandler(videojs);
  }

  dispose() {
    this.player.srOptions_ = undefined;

    const tech = this.player.tech(true);
    if (tech.hlsProvider) {
      tech.hlsProvider.dispose();
      tech.hlsProvider = undefined;
    }

    super.dispose();
  }
}

videojs.registerPlugin("hlsjs", HLSJSConfigHandler);

// ---------------------------------------------------------------------------
// HLS JS source handler
// ---------------------------------------------------------------------------

export class Html5Hlsjs {
  static hooks = {};

  errorCounts = {};

  maxNetworkErrorRecovery = 5;

  hlsjsConfig = null;

  _duration = null;
  metadata = null;
  isLive = null;
  dvrDuration = null;
  edgeMargin = null;

  handlers = {
    play: null,
    error: null
  };

  constructor(vjs, source, tech) {
    this.vjs = vjs;
    this.source = source;

    this.tech = tech;
    this.tech.name_ = "Hlsjs";

    this.videoElement = tech.el();
    this.player = vjs(tech.options_.playerId);

    this.handlers.error = event => {
      let errorTxt;
      const mediaError = (event.currentTarget || event.target).error;

      if (!mediaError) return;

      console.log(mediaError);
      switch (mediaError.code) {
        case mediaError.MEDIA_ERR_ABORTED:
          errorTxt = "You aborted the video playback";
          break;
        case mediaError.MEDIA_ERR_DECODE:
          errorTxt =
            "The video playback was aborted due to a corruption problem or because the video used features " +
            "your browser did not support";
          this._handleMediaError(mediaError);
          break;
        case mediaError.MEDIA_ERR_NETWORK:
          errorTxt =
            "A network error caused the video download to fail part-way";
          break;
        case mediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
          errorTxt =
            "The video could not be loaded, either because the server or network failed or because the format is not supported";
          break;

        default:
          errorTxt = mediaError.message;
      }

      console.error(`MEDIA_ERROR: ${errorTxt}`);
    }
    this.videoElement.addEventListener("error", this.handlers.error);

    this.initialize();
  }

  duration() {
    if (this._duration === Infinity) return Infinity;
    if (!isNaN(this.videoElement.duration)) return this.videoElement.duration;

    return this._duration || 0;
  }

  seekable() {
    if (this.hls.media) {
      if (!this.isLive) {
        return this.vjs.createTimeRanges(0, this.hls.media.duration);
      }

      // Video.js doesn't seem to like floating point timeranges
      const startTime = Math.round(this.hls.media.duration - this.dvrDuration);
      const endTime = Math.round(this.hls.media.duration - this.edgeMargin);

      return this.vjs.createTimeRanges(startTime, endTime);
    }

    return this.vjs.createTimeRanges();
  }

  // See comment for `initialize` method.
  dispose() {
    this.videoElement.removeEventListener("play", this.handlers.play);
    this.videoElement.removeEventListener("error", this.handlers.error);

    // FIXME: https://github.com/video-dev/hls.js/issues/4092
    const untypedHLS = this.hls;
    untypedHLS.log = untypedHLS.warn = () => {
      // empty
    }

    this.hls.destroy();
  }

  static addHook(type, callback) {
    Html5Hlsjs.hooks[type] = this.hooks[type] || [];
    Html5Hlsjs.hooks[type].push(callback);
  }

  static removeHook(type, callback) {
    if (Html5Hlsjs.hooks[type] === undefined) return false;

    const index = Html5Hlsjs.hooks[type].indexOf(callback);
    if (index === -1) return false;

    Html5Hlsjs.hooks[type].splice(index, 1);

    return true;
  }

  static removeAllHooks() {
    Html5Hlsjs.hooks = {};
  }

  _executeHooksFor(type) {
    if (Html5Hlsjs.hooks[type] === undefined) {
      return;
    }

    // ES3 and IE < 9
    for (let i = 0; i < Html5Hlsjs.hooks[type].length; i++) {
      Html5Hlsjs.hooks[type][i](this.player, this.hls);
    }
  }

  _getHumanErrorMsg(error) {
    switch (error.code) {
      default:
        return error.message;
    }
  }

  _handleUnrecovarableError(error) {
    if (this.hls.levels.filter(l => l.id > -1).length > 1) {
      this._removeQuality(this.hls.loadLevel);
      return;
    }

    this.hls.destroy();
    console.log("bubbling error up to VIDEOJS");
    this.tech.error = () => ({
      ...error,
      message: this._getHumanErrorMsg(error)
    });
    this.tech.trigger("error");
  }

  _handleMediaError(error) {
    if (this.errorCounts[Hls.ErrorTypes.MEDIA_ERROR] === 1) {
      console.log("trying to recover media error");
      this.hls.recoverMediaError();
      return;
    }

    if (this.errorCounts[Hls.ErrorTypes.MEDIA_ERROR] === 2) {
      console.log("2nd try to recover media error (by swapping audio codec");
      this.hls.swapAudioCodec();
      this.hls.recoverMediaError();
      return;
    }

    if (this.errorCounts[Hls.ErrorTypes.MEDIA_ERROR] > 2) {
      this._handleUnrecovarableError(error);
    }
  }

  _handleNetworkError(error) {
    if (navigator.onLine === false) return;

    if (
      this.errorCounts[Hls.ErrorTypes.NETWORK_ERROR] <=
      this.maxNetworkErrorRecovery
    ) {
      console.log("trying to recover network error");

      // Wait 1 second and retry
      setTimeout(() => this.hls.startLoad(), 1000);

      // Reset error count on success
      this.hls.once(Hls.Events.FRAG_LOADED, () => {
        this.errorCounts[Hls.ErrorTypes.NETWORK_ERROR] = 0;
      })

      return;
    }

    this._handleUnrecovarableError(error);
  }

  _onError(_event, data) {
    const error = {
      message: `HLS.js error: ${data.type} - fatal: ${data.fatal} - ${data.details}`
    };

    // increment/set error count
    if (this.errorCounts[data.type]) this.errorCounts[data.type] += 1;
    else this.errorCounts[data.type] = 1;

    if (data.fatal)
      console.error(error.message, {
        currentTime: this.player.currentTime(),
        data
      });
    else console.log(error.message);

    if (data.type === Hls.ErrorTypes.NETWORK_ERROR) {
      error.code = 2;
      this._handleNetworkError(error);
    } else if (
      data.fatal &&
      data.type === Hls.ErrorTypes.MEDIA_ERROR &&
      data.details !== "manifestIncompatibleCodecsError"
    ) {
      error.code = 3;
      this._handleMediaError(error);
    } else if (data.fatal) {
      this._handleUnrecovarableError(error);
    }
  }

  buildLevelLabel(level) {
    if (this.player.srOptions_.levelLabelHandler) {
      return this.player.srOptions_.levelLabelHandler(level);
    }

    if (level.height) return level.height + "p";
    if (level.width) return Math.round((level.width * 9) / 16) + "p";
    if (level.bitrate) return level.bitrate / 1000 + "kbps";

    return "0";
  }

  _removeQuality(index) {
    this.hls.removeLevel(index);
    this.player.peertubeResolutions().remove(index);
    this.hls.currentLevel = -1;
  }

  _notifyVideoQualities() {
    if (!this.metadata) return;

    const resolutions = [];

    this.metadata.levels.forEach((level, index) => {
      resolutions.push({
        id: index,
        height: level.height,
        width: level.width,
        bitrate: level.bitrate,
        label: this.buildLevelLabel(level),
        selected: level.id === this.hls.manualLevel,

        selectCallback: () => {
          this.hls.currentLevel = index
        }
      });
    })

    resolutions.push({
      id: -1,
      label: this.player.localize("Auto"),
      selected: true,
      selectCallback: () => (this.hls.currentLevel = -1)
    });

    this.player.peertubeResolutions().add(resolutions);
  }

  _startLoad() {
    this.hls.startLoad(-1);
    this.videoElement.removeEventListener("play", this.handlers.play);
  }

  _oneLevelObjClone(obj) {
    const result = {};
    const objKeys = Object.keys(obj);
    for (let i = 0; i < objKeys.length; i++) {
      result[objKeys[i]] = obj[objKeys[i]];
    }

    return result;
  }

  _onMetaData(_event, data) {
    // This could arrive before 'loadedqualitydata' handlers is registered, remember it so we can raise it later
    this.metadata = data;
    this._notifyVideoQualities();
  }

  _initHlsjs() {
    const techOptions = this.tech.options_;
    const srOptions_ = this.player.srOptions_;

    const hlsjsConfigRef = srOptions_?.hlsjsConfig || techOptions.hlsjsConfig;
    // Hls.js will write to the reference thus change the object for later streams
    this.hlsjsConfig = hlsjsConfigRef
      ? this._oneLevelObjClone(hlsjsConfigRef)
      : {};

    if (
      ["", "auto"].includes(this.videoElement.preload) &&
      !this.videoElement.autoplay &&
      this.hlsjsConfig.autoStartLoad === undefined
    ) {
      this.hlsjsConfig.autoStartLoad = false;
    }

    // If the user explicitly sets autoStartLoad to false, we're not going to enter the if block above
    // That's why we have a separate if block here to set the 'play' listener
    if (this.hlsjsConfig.autoStartLoad === false) {
      this.handlers.play = this._startLoad.bind(this);
      this.videoElement.addEventListener("play", this.handlers.play);
    }

    this.hls = new Hls(this.hlsjsConfig);

    this._executeHooksFor("beforeinitialize");

    this.hls.on(Hls.Events.ERROR, (event, data) => this._onError(event, data));
    this.hls.on(Hls.Events.MANIFEST_PARSED, (event, data) =>
      this._onMetaData(event, data)
    );
    this.hls.on(Hls.Events.LEVEL_LOADED, (event, data) => {
      // The DVR plugin will auto seek to "live edge" on start up
      if (this.hlsjsConfig.liveSyncDuration) {
        this.edgeMargin = this.hlsjsConfig.liveSyncDuration;
      } else if (this.hlsjsConfig.liveSyncDurationCount) {
        this.edgeMargin = this.hlsjsConfig.liveSyncDurationCount * data.details.targetduration;
      }

      this.isLive = data.details.live;
      this.dvrDuration = data.details.totalduration;

      this._duration = this.isLive ? Infinity : data.details.totalduration;

      // Increase network error recovery for lives since they can be broken (server restart, stream interruption etc)
      if (this.isLive) this.maxNetworkErrorRecovery = 30;
    });

    this.hls.once(Hls.Events.FRAG_LOADED, () => {
      // Emit custom 'loadedmetadata' event for parity with `videojs-contrib-hls`
      // Ref: https://github.com/videojs/videojs-contrib-hls#loadedmetadata
      this.tech.trigger("loadedmetadata");
    });

    this.hls.on(Hls.Events.LEVEL_SWITCHING, (_e, data) => {
      const resolutionId = this.hls.autoLevelEnabled ? -1 : data.level;

      const autoResolutionChosenId = this.hls.autoLevelEnabled ? data.level : -1;

      this.player
        .peertubeResolutions()
        .select({
          id: resolutionId,
          autoResolutionChosenId,
          fireCallback: false
        });
    });

    this.hls.attachMedia(this.videoElement);

    this.hls.loadSource(this.source.src);
  }

  initialize() {
    this._initHlsjs();
  }
}
