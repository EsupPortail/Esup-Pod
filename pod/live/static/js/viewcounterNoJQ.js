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

document.addEventListener("DOMContentLoaded", function () {
  let podplayer = videojs("podvideoplayer");
  podplayer.ready(function () {
    let secret = makeid(24);
    (async function () {
      let url =
        "/live/ajax_calls/heartbeat/?key=" +
        secret +
        "&liveid=" +
        document.getElementById("livename").dataset.liveid;
      await fetch(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        cache: false,
      })
        .then((response) => response.json())
        .then((response) => {
          document.getElementById("viewers-ul").innerHTML = "";
          document.getElementById("viewcount").textContent = response.viewers;
          response.viewers_list.forEach((view) => {
            let name = view.first_name + " " + view.last_name;
            if (name == " ") {
              name = "???";
            }
            document
              .getElementById("viewers-ul")
              .append("<li>" + name + "</li>");
          });
        });
      setTimeout(arguments.callee, heartbeat_delay * 1000);
    });
  })();

  function resizeViewerList() {
    document.getElementById("viewers-list").style.width =
      0.3 * document.getElementById("podvideoplayer").clientWidth + "";
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
        videojs.dom.classList.add(this.el(), "vjs-info-button");
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
      let menu = document.getElementById("viewers-list");
      if (
        menu.style.display == "none" &&
        document.getElementById("viewers-ul").childNodes.length > 0
      ) {
        menu.style.display = "block";
      } else {
        menu.style.display = "none";
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
