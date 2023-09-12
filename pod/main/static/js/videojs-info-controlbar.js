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

    /*
     * Info menu button
     */
    var MenuButton = videojs.getComponent("Button");

    class InfoMenuButton extends MenuButton {
      constructor(player, options) {
        options.label = "Info";
        MenuButton.call(this, player, options);
        this.el().setAttribute("aria-label", "Info");
        videojs.dom.addClass(this.el(), "vjs-info-button");
        this.controlText("Information");
      }
    };
    InfoMenuButton.prototype.handleClick = function (event) {
      MenuButton.prototype.handleClick.call(this, event);
      show_info_video();
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
