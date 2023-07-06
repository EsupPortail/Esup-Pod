(function () {
  "use strict";
  var videojs = null;
  if (typeof window.videojs === "undefined" && typeof require === "function") {
    videojs = require("video.js");
  } else {
    videojs = window.videojs;
  }

  (function (window, videojs) {
    var videoJsLogo,
      defaults = {
        ui: true,
      };

    /*
     * Logo menu button
     */
    var MenuButton = videojs.getComponent("Button");

    var LogoMenuButton = videojs.extend(MenuButton, {
      constructor: function (player, options) {
        options.label = "Logo";
        MenuButton.call(this, player, options);
        this.el().setAttribute("aria-label", options.linktitle);
        this.controlText(options.linktitle);
        videojs.dom.addClass(this.el(), "vjs-logo-button");
        this.el().setAttribute(
          "style",
          "background-image: url(" +
            options.imgsrc +
            "); background-repeat: no-repeat;  background-position: center; ",
        );
        this.link = options.link;
      },
    });
    LogoMenuButton.prototype.handleClick = function (event) {
      MenuButton.prototype.handleClick.call(this, event);
      if (this.link == "") window.open("/", "_blank");
      else window.open(this.link, "_blank");
    };
    MenuButton.registerComponent("LogoMenuButton", LogoMenuButton);

    /**
     * Initialize the plugin.
     */
    videoJsLogo = function (options) {
      var settings = videojs.mergeOptions(defaults, options),
        player = this;
      player.ready(function () {
        if (settings.ui) {
          var menuButton = new LogoMenuButton(player, settings);
          player.controlBar.logo = player.controlBar.el_.appendChild(
            menuButton.el_,
          );
          player.controlBar.logo.dispose = function () {
            this.parentNode.removeChild(this);
          };
        }
      });
    };

    // Register the plugin
    videojs.registerPlugin("videoJsLogo", videoJsLogo);
  })(window, videojs);
})();
