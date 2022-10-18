function makeid(length) {
  var result = "";
  var characters =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  var charactersLength = characters.length;
  for (var i = 0; i < length; i++) {
    result += characters.charAt(Math.floor(Math.random() * charactersLength));
  }
  return result;
}

$(document).ready(function () {
  let podplayer = videojs("podvideoplayer");
  podplayer.ready(function () {
    let secret = makeid(24);
    (function () {
      $.ajax({
        type: "GET",
        url:
          "/live/ajax_calls/heartbeat/?key=" +
          secret +
          "&liveid=" +
          $("#livename").data("liveid"),
        cache: false,
        success: function (response) {
          $("#viewers-ul").html("");
          $("#viewcount").text(response.viewers);
          response.viewers_list.forEach((view) => {
            let name = view.first_name + " " + view.last_name;
            if (name == " ") {
              name = "???";
            }
            $("#viewers-ul").append("<li>" + name + "</li>");
          });
        },
      });

      setTimeout(arguments.callee, heartbeat_delay * 1000);
    })();
  });

  function resizeViewerList() {
    $("#viewers-list").css("width", 0.3 * $("#podvideoplayer").width());
  }
  window.onresize = resizeViewerList;
  resizeViewerList();
});

(function () {
  "use strict";
  var videojs = null;
  if (typeof window.videojs === "undefined" && typeof require === "function") {
    videojs = require("video.js");
  } else {
    videojs = window.videojs;
  }

  (function (window, videojs) {
    var videoJsViewerCount,
      defaults = {
        ui: true,
        innerHTML: "test",
      };

    /*
     * Chapter menu button
     */
    var MenuButton = videojs.getComponent("Button");

    var InfoMenuButton = videojs.extend(MenuButton, {
      constructor: function (player, options) {
        options.label = "Viewers";
        MenuButton.call(this, player, options);
        this.el().setAttribute("aria-label", "Viewers");
        videojs.dom.addClass(this.el(), "vjs-info-button");
        this.controlText("Viewers");
        //because sometimes doesn't
        let eyeSVG =
          '<svg id="view-counter-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="align-bottom" color="red"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>';
        this.el().innerHTML =
          '<span style="line-height:1.7">' +
          eyeSVG +
          '<span style="padding-left:4px" id="viewcount">?</div></span></span>';
      },
    });
    InfoMenuButton.prototype.handleClick = function (event) {
      MenuButton.prototype.handleClick.call(this, event);
      if (
        $("#viewers-list").css("display") == "none" &&
        $("#viewers-ul").children().length > 0
      ) {
        $("#viewers-list").css("display", "block");
      } else {
        $("#viewers-list").css("display", "none");
      }
    };
    MenuButton.registerComponent("InfoMenuButton", InfoMenuButton);

    /**
     * Initialize the plugin.
     */
    videoJsViewerCount = function (options) {
      var settings = videojs.mergeOptions(defaults, options),
        player = this;
      player.ready(function () {
        if (settings.ui) {
          var menuButton = new InfoMenuButton(player, settings);
          player.controlBar.info = player.controlBar.el_.appendChild(
            menuButton.el_
          );
          player.controlBar.info.dispose = function () {
            this.parentNode.removeChild(this);
          };
        }
      });
    };

    // Register the plugin
    videojs.registerPlugin("videoJsViewerCount", videoJsViewerCount);
  })(window, videojs);
})();
