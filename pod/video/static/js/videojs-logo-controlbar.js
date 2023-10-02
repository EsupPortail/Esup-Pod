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
     * Logo menu link
     */
    var MenuLink = videojs.getComponent("ClickableComponent");

    class LogoMenuLink extends MenuLink {
      constructor(player, options) {
        var aElement = document.createElement("a");
        // console.log(options.link);
        if (options.link && options.link !== "") {
          aElement.href = options.link;
        } else {
          aElement.href = "/";
        }
        aElement.target = "_blank";
        aElement.setAttribute("aria-label", options.linktitle);
        aElement.setAttribute("title", options.linktitle);
        aElement.classList.add("vjs-logo-button", "vjs-control");
        aElement.setAttribute(
          "style",
          "background-image: url(" +
            options.imgsrc +
            "); background-repeat: no-repeat; background-position: center; cursor: pointer;",
        );
        super(player, { el: aElement });
      }
    }

    /**
     * Initialize the plugin.
     */
    videoJsLogo = function (options) {
      var settings = videojs.mergeOptions(defaults, options),
        player = this;
      player.ready(function () {
        if (settings.ui) {
          var menuLink = new LogoMenuLink(player, settings);
          player.controlBar.logo = player.controlBar.el_.appendChild(
            menuLink.el(),
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
