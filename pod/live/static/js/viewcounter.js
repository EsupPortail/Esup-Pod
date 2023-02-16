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

function resizeViewerList() {
  let desired_width =
    0.3 * document.getElementById("podvideoplayer").offsetWidth;
  document.getElementById("viewers-list").style.width = desired_width + "px";
}

document.addEventListener("DOMContentLoaded", function () {
  let podplayer = videojs("podvideoplayer");

  podplayer.ready(function () {
    let secret = makeid(24);

    let live_element = document.getElementById("livename");

    let param;
    if (live_element.dataset.broadcasterid !== undefined)
      param = "&broadcasterid=" + live_element.dataset.broadcasterid;
    else if (live_element.dataset.eventid !== undefined)
      param = "&eventid=" + live_element.dataset.eventid;

    let url = "/live/ajax_calls/heartbeat/?key=" + secret + param;

    function sendHeartBeat() {
      fetch(url, {
        method: "GET",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
      })
        .then((response) => {
          if (response.ok) return response.json();
          else return Promise.reject(response);
        })
        .then((result) => {
          let names = "";
          result.viewers_list.forEach((viewer) => {
            let name = viewer.first_name + " " + viewer.last_name;
            if (name === " ") {
              name = "?";
            }
            names += "<li>" + name + "</li>";
          });

          document.getElementById("viewcount").innerHTML = result.viewers;
          document.getElementById("viewers-ul").innerHTML = names;
        })
        .catch((error) => {
          console.log("Impossible to get viewers list. ", error.message);
        });
    }

    // Heartbeat sent every x seconds
    setInterval(sendHeartBeat, heartbeat_delay * 1000);

    window.onresize = resizeViewerList;
  });
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
      let viewer_list_el = document.getElementById("viewers-list");

      if (
        viewer_list_el.style.display === "none" &&
        document.getElementById("viewers-ul").children.length > 0
      ) {
        viewer_list_el.style.display = "block";
      } else {
        viewer_list_el.style.display = "none";
      }

      if (viewer_list_el.style.width === "0px") {
        resizeViewerList();
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
