(function () {
  "use strict";
  var videojs = null;
  if (typeof window.videojs === "undefined" && typeof require === "function") {
    videojs = require("video.js");
  } else {
    videojs = window.videojs;
  }

  (function (window, videojs) {
    var defaults = {
      ui: true,
    };

    /*
     * Chapter menu button
     */
    var MenuButton = videojs.getComponent("MenuButton");
    class ChapterMenuButton extends MenuButton {
      constructor(player, options) {
        options.label = gettext("Chapters");
        super(player, options);
        this.el().setAttribute("aria-label", gettext("Chapters"));
        videojs.dom.addClass(this.el(), "vjs-chapters-button");
        this.controlText(gettext("Chapters"));

        var span = document.createElement("span");
        videojs.dom.addClass(span, "vjs-chapters-icon");
        this.el().appendChild(span);
      }
      handleClick(event) {
        MenuButton.prototype.handleClick.call(this, event);
        if (
          document.querySelectorAll(".chapters-list.inactive li").length > 0
        ) {
          document
            .querySelector(".chapters-list.inactive")
            .setAttribute("class", "chapters-list active");
          document.querySelector(".vjs-chapters-button button").style =
            "text-shadow: 0 0 1em #fff";
        } else {
          document
            .querySelector(".chapters-list.active")
            .setAttribute("class", "chapters-list inactive");

          document.querySelector(".vjs-chapters-button button").style =
            "text-shadow: '' ";
        }
      }
    }
    MenuButton.registerComponent("ChapterMenuButton", ChapterMenuButton);

    /**
     * Initialize the plugin.
     */
    var Plugin = videojs.getPlugin("plugin");

    /**
     * Custom Video.js plugin for handling chapters in a video player.
     *
     * @class podVideoJsChapters
     * @extends {Plugin}
     * @param {Object} player - The Video.js player instance.
     * @param {Object} options - Configuration options for the plugin.
     */
    class podVideoJsChapters extends Plugin {
      constructor(player, options) {
        super(player, options);
        var settings = videojs.obj.merge(defaults, options),
          chapters = {},
          currentChapter = document.createElement("li");

        /**
         * Create the list of chapters.
         *
         * @memberof podVideoJsChapters
         * @param {Array} data - Chapter data to be displayed.
         * @returns {boolean} - Returns false if no chapter data is provided.
         */
        player.createChapters = function (data) {
          if (!data) {
            return false;
          }
          this.chapters = groupedChapters(data);

          var ol = document.getElementById("chapters-list");
          for (var i = 0; i < this.chapters.id.length; ++i) {
            var chapId = this.chapters.id[i];
            var chapTitle = this.chapters.title[i];
            var chapTime = this.chapters.start[i];
            var newLi = document.createElement("li");
            var newA = document.createElement("a");
            newA.setAttribute("id", "chapter" + chapId);
            newA.setAttribute("start", chapTime);
            newA.setAttribute("role", "button");
            newA.setAttribute("tabindex", "0");

            var newTitle = document.createTextNode(chapTitle);
            newA.appendChild(newTitle);
            newLi.appendChild(newA);
            ol.appendChild(newLi);

            newA.addEventListener(
              "click",
              function () {
                player.currentTime(this.attributes.start.value);
              },
              false,
            );
          }
        };

        /**
         * Return a list of chapters usable by other functions.
         *
         * @memberof podVideoJsChapters
         * @param {Array} data - Chapter data to be grouped.
         * @returns {Object} - Object containing arrays of chapter information.
         */
        function groupedChapters(data) {
          var chapters = {
            id: [],
            title: [],
            start: [],
          };
          for (var i = 0; i < data.length; i++) {
            chapters.id.push(parseInt(data[i].attributes[1].value));
            chapters.title.push(data[i].attributes[2].value);
            chapters.start.push(parseInt(data[i].attributes[0].value));
          }
          return chapters;
        }

        /**
         * Get the grouped chapters.
         *
         * @memberof podVideoJsChapters
         * @returns {Object} - Object containing arrays of chapter information.
         */
        player.getGroupedChapters = function () {
          return this.chapters;
        };

        /**
         * Update the current chapter based on the current time.
         *
         * @memberof podVideoJsChapters
         * @param {number} time - Current time in seconds.
         * @param {Object} chapters - Object containing arrays of chapter information.
         */
        player.getCurrentChapter = function (time, chapters) {
          const currentTime = Math.floor(time);

          var keys = Object.keys(chapters.start);
          for (let i = 0; i <= keys.length - 1; i++) {
            var next = chapters.start[i + 1] || player.duration();
            currentChapter = document.getElementById(
              "chapter" + chapters.id[i],
            );
            if (currentTime >= chapters.start[i] && currentTime < next) {
              currentChapter.classList.add("current");
            } else {
              currentChapter.classList.remove("current");
            }
          }
        };

        /**
         * Main function for initializing the plugin.
         *
         * @memberof podVideoJsChapters
         */
        player.main = function () {
          var data = document.querySelectorAll("#chapters li");
          if (
            settings.ui &&
            data.length >= 1 &&
            typeof player.controlBar.chapters == "undefined"
          ) {
            var menuButton = new ChapterMenuButton(player, settings);
            player.controlBar.chapters = player.controlBar.el_.insertBefore(
              menuButton.el_,
              player.controlBar.getChild("fullscreenToggle").el_,
            );
            player.controlBar.chapters.dispose = function () {
              this.parentNode.removeChild(this);
              player.controlBar.chapters = undefined;
            };
          }
          if (data.length >= 1) {
            player.createChapters(data);
          }

          let podPlayer = document.getElementById(player.id());
          let chapters_list = document.querySelectorAll(".chapters-list");
          if (chapters_list.length > 0) {
            chapters_list.forEach((element) => {
              podPlayer.appendChild(element);
            });
          }
        };

        player.ready(player.main);

        this.on(player, "timeupdate", function () {
          player.getCurrentChapter(
            player.currentTime(),
            player.getGroupedChapters(),
          );
        });
      }
    }

    podVideoJsChapters.prototype.dispose = function () {
      Plugin.prototype.dispose.call(this);
    };

    // Register the plugin
    videojs.registerPlugin("podVideoJsChapters", podVideoJsChapters);
  })(window, videojs);
})();
