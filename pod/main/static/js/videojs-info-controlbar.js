/**
 * @file Esup-Pod functions for managing video.js information panel.
 * @since 2.0.0
 */

// Read-only globals defined in video-script.html
/*
global player
*/

// Global vars
const hdres = 1920 / 1080;
let isPlaying = false;
let wasPlaying = false;

/**
 * Show or Hide the Pod video information panel (Called by video-iframe)
 */
function showInfoVideo() {
  const hasStarted = player.el().classList.contains("vjs-has-started");
  const isOverlayed = document
    .getElementById("div-video-wrapper")
    .classList.contains("overlay");
  const isInfoOverlayed =
    isOverlayed &&
    document.getElementById("div-video-wrapper").classList.contains("info");
  const cls = "overlay info";
  if (!isOverlayed) {
    // No overlay is displayed
    wasPlaying = isPlaying;
    player.pause();
    document.getElementById("div-video-wrapper").className = cls;
    resizeInfo();
  } else if (!isInfoOverlayed) {
    // One overlay is displayed but not Info
    document.getElementById("div-video-wrapper").className = cls;
    resizeInfo();
  } else {
    // Info overlay is displayed => close
    document.getElementById("div-video-wrapper").className = hasStarted
      ? ""
      : "vjs-not-started";
    if (wasPlaying) player.play();
  }
}

/**
 * Resize responsively the Pod video Information panel
 */
function resizeInfo() {
  const ihead = document.querySelector("#info-video-wrapper > .iframe-header");
  const ph = player.el().offsetHeight;
  const pb = parseInt(player.el().style.top) + ph - 30;
  const pw = ph * hdres; // ('#podvideoplayer .vjs-poster').width()
  document.getElementById("info-video").style.top = ihead.offsetHeight + "px";
  // console.log('MTop: '+player.el().style.top+'\nleft: '+player.el().offsetLeft+'\nwidth: '+player.el().offsetWidth+'\nheight: '+player.el().offsetHeight+' /// '+pb)
  document.getElementById("info-video-wrapper").cssText =
    "top:" +
    player.el().style.top +
    ", height:" +
    (ph - 30) +
    "px, left: '50%', 'margin-left':" +
    -(pw / 2) +
    "px, width:" +
    pw +
    "px";
  document.getElementById("overlay-footer").style.top = pb + "px";
}

/**
 * Resize responsively the video.js player (Called by video-iframe.html)
 */
function resizeVideoJs() {
  const width = document.getElementById(player.id()).parentElement.offsetWidth;
  const height = document.getElementById(player.id()).parentElement
    .offsetHeight;
  const ratio = width / height;
  let margintop = 0;
  if (ratio < hdres) {
    player.width(width);
    player.height(width / hdres);
    margintop = parseInt((height - player.height()) / 2);
    document.getElementById("podvideoplayer").style.top = margintop + "px";
  } else {
    player.height(height);
    player.width(height * hdres);
    document.getElementById("podvideoplayer").style.top = "0";
  }
  resizeInfo();
}

(function () {
  "use strict";
  var videojs = null;
  if (typeof window.videojs === "undefined" && typeof require === "function") {
    videojs = require("video.js");
  } else {
    videojs = window.videojs;
  }

  (function (window, videojs) {
    var videoJsInfo,
      defaults = {
        ui: true,
      };

    var MenuButton = videojs.getComponent("Button");

    /**
     * Info menu button for video.js
     */
    class InfoMenuButton extends MenuButton {
      constructor(player, options) {
        options.label = gettext("Info");
        super(player, options);
        this.el().setAttribute("aria-label", options.label);
        videojs.dom.addClass(this.el(), "vjs-info-button");
        this.controlText(gettext("Information"));
      }
    }
    InfoMenuButton.prototype.handleClick = function (event) {
      MenuButton.prototype.handleClick.call(this, event);
      showInfoVideo();
    };
    MenuButton.registerComponent("InfoMenuButton", InfoMenuButton);

    /**
     * Initialize the plugin.
     */
    videoJsInfo = function (options) {
      var settings = videojs.mergeOptions(defaults, options),
        player = this;
      player.ready(function () {
        if (settings.ui) {
          var menuButton = new InfoMenuButton(player, settings);
          player.controlBar.info = player.controlBar.el_.appendChild(
            menuButton.el_,
          );
          player.controlBar.info.dispose = function () {
            this.parentNode.removeChild(this);
          };
        }
      });
    };

    // Register the plugin
    videojs.registerPlugin("videoJsInfo", videoJsInfo);
  })(window, videojs);
})();
