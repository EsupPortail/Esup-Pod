(function () {
  "use strict";
  var videojs = null;
  if (typeof window.videojs === "undefined" && typeof require === "function") {
    videojs = require("video.js");
  } else {
    videojs = window.videojs;
  }

  (function (window, videojs) {
    var videoJsPlaylist,
      defaults = {
        ui: true,
      };

    /*
     * Playlist menu button
     */
    var MenuButton = videojs.getComponent("Button");

    var PlaylistMenuButton = videojs.extend(MenuButton, {
      constructor: function (player, options) {
        options.label = "Playlist";
        MenuButton.call(this, player, options);
        this.el().setAttribute("aria-label", "Playlist");
        videojs.dom.addClass(this.el(), "vjs-playlist-button");
        this.controlText("Playlist");
      },
    });
    PlaylistMenuButton.prototype.handleClick = function (event) {
      MenuButton.prototype.handleClick.call(this, event);
      show_video_playlist();
    };
    MenuButton.registerComponent("PlaylistMenuButton", PlaylistMenuButton);

    /**
     * Initialize the plugin.
     */
    videoJsPlaylist = function (options) {
      var settings = videojs.mergeOptions(defaults, options),
        player = this;
      player.ready(function () {
        if (settings.ui) {
          var menuButton = new PlaylistMenuButton(player, settings);
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
    videojs.registerPlugin("videoJsPlaylist", videoJsPlaylist);
  })(window, videojs);
})();
