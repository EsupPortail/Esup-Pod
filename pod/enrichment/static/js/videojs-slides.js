"use-strict";
//// Begin Safari patch for enrich track
var loadEnrichmentVTTfile = function (url, callback) {
  var getXhr = function () {
      try {
        return new XMLHttpRequest();
      } catch (e) {
        try {
          return new ActiveXObject("Msxml3.XMLHTTP");
        } catch (e) {
          try {
            return new ActiveXObject("Msxml2.XMLHTTP.6.0");
          } catch (e) {
            try {
              return new ActiveXObject("Msxml2.XMLHTTP.3.0");
            } catch (e) {
              try {
                return new ActiveXObject("Msxml2.XMLHTTP");
              } catch (e) {
                try {
                  return new ActiveXObject("Microsoft.XMLHTTP");
                } catch (e) {
                  return null;
                }
              }
            }
          }
        }
      }
    },
    timeInSecond = function (strtime) {
      let atime = strtime.split(":");
      return (
        parseInt(atime[0]) * 3600 + parseInt(atime[1]) * 60 + parseInt(atime[2])
      );
    },
    createEmptyCue = function (start, end) {
      return {
        title: "",
        url: "",
        type: "",
        stop_video: 0,
        start: start,
        end: end,
      };
    },
    setCue = function (index, data) {
      cues[index].title = data.title;
      cues[index].url = data.url;
      cues[index].type = data.type;
      cues[index].stop_video = data.stop_video;
    },
    cues = new Array(),
    xhr = getXhr();
  if (null != xhr) {
    xhr.open("GET", url, true);
    xhr.onreadystatechange = function () {
      if (this.readyState == 4) {
        var lines = xhr.responseText.split("\n"),
          nbl = lines.length,
          reg =
            /(^\d{2}:\d{2}:\d{2})\.\d{3} \-\-> (\d{2}:\d{2}:\d{2})\.\d{3}$/i,
          fisrtcueline = 1,
          txtdata = "",
          c = 0;
        //// Check WebVTT
        if (lines[0].substr(0, 6) != "WEBVTT") {
          callback(cues);
          return false;
        }
        //// Get First cue line and create first cue
        for (let i = 1; i < nbl; i++) {
          if ((m = lines[i].match(reg))) {
            fisrtcueline = i;
            cues[c] = createEmptyCue(timeInSecond(m[1]), timeInSecond(m[2])); //console.log('Cue '+c+' is created');
            break;
          }
        }
        //// Read next lines, feed first, create and feed next cues
        for (let i = fisrtcueline + 1; i < nbl; i++) {
          if ((m = lines[i].match(reg))) {
            setCue(c, JSON.parse(txtdata.split("}")[0] + "}"));
            txtdata = "";
            c++;
            cues[c] = createEmptyCue(timeInSecond(m[1]), timeInSecond(m[2])); //console.log('Cue '+c+' is created');
          } else {
            txtdata += lines[i];
          }
        }
        //// Feed last cue
        setCue(c, JSON.parse(txtdata));
        //// Callback cues
        callback(cues);
      }
    };
    xhr.send();
  } else {
    callback(null);
  }
};
//// End Safari patch for enrich track

var videojs = window.videojs;

const slides_defaults = {};
const registerSlidePlugin = videojs.registerPlugin || videojs.plugin;
const slide_color = {
  document: "var(--bs-orange)",
  image: "var(--bs-purple)",
  richtext: "var(--bs-blue)",
  weblink: "var(--bs-red)",
  embed: "var(--bs-green)",
};
//Is now a list of css class instead of video/slide width values
const split_slide_label = gettext("Split view");
const split_slide = "split-slide";
const no_slide_label = gettext("slide off");
const no_slide = "no-slide";
const pip_slide_label = gettext("pip media");
const pip_slide = "pip-slide";
const pip_video_label = gettext("pip video");
const pip_video = "big-slide";
const full_slide_label = gettext("video off");
const full_slide = "full-slide";
// no really understood the meaning of putting key of dict in []...
const slide_mode_list = {
  [no_slide]: no_slide_label,
  [split_slide]: split_slide_label,
  [pip_slide]: pip_slide_label,
  [pip_video]: pip_video_label,
  [full_slide]: full_slide_label,
};

var default_slide_mode = split_slide;
var current_slide_mode = split_slide;
var currentSlide = null;

/**
 * VideoSlides component
 *
 * @class VideoSlides
 * @extends {videojs.Component}
 */
var VideoSlides = function (items) {
  /**
   * AppendSlider function to append Slide list into VideoJS.
   *
   * @return {void} doesn't return anything
   * @function appendSlider
   */
  this.appendSlider = function () {
    // Get control bar element
    const controlBar = document.getElementsByClassName("vjs-control-bar")[0];

    // Add slide list className
    this.slides.className = "video-slides";
    controlBar.parentNode.insertBefore(this.slides, controlBar);
    this.appendSliderItem();
    this.slideBar();
  };

  /**
   * AppendSliderItem function to append SlideItem into Slide List.
   *
   * @return {void} doesn't return anything
   * @function appendSliderItem
   */
  this.appendSliderItem = function () {
    var keys = Object.keys(this.slidesItems);
    for (let i = 0; i <= keys.length - 1; i++) {
      // Create the slide depend on their type
      var type = this.slidesItems[i].type;
      var slide = null;
      /*if (type == 'image') {
                        slide = document.createElement('img');
                        slide.src = this.slidesItems[i].url;
                        slide.alt = this.slidesItems[i].title;
                        slide.width = player.currentDimensions().width / 2;
                        slide.height = player.currentDimensions().height / 2;
                } else*/
      if (type == "document") {
        slide = document.createElement("embed");
        slide.src = this.slidesItems[i].url;
        slide.alt = this.slidesItems[i].title;
        slides.type = "application/pdf";
        slide.width = "100%"; //player.currentDimensions().width / 2;
        slide.height = "100%"; //player.currentDimensions().height / 2;
      } else if (type == "richtext") {
        slide = document.createElement("div");
        slide.innerHTML = this.slidesItems[i].url;
      } else if (type == "weblink") {
        slide = document.createElement("embed");
        slide.src = this.slidesItems[i].url;
        slide.alt = this.slidesItems[i].title;
        slides.type = "text/html";
        slide.width = "100%"; //player.currentDimensions().width / 2;
        slide.height = "100%"; //player.currentDimensions().height / 2;
      } else if (type == "embed") {
        slide = document.createElement("div");
        slide.classList.add("slide_embed");
        slide.innerHTML = this.slidesItems[i].url;
      }
      const li = document.createElement("li");
      // Added src and class name
      li.setAttribute("data-start", this.slidesItems[i].start);
      li.setAttribute("data-end", this.slidesItems[i].end);
      li.setAttribute("data-type", this.slidesItems[i].type);
      li.setAttribute("data-stop", this.slidesItems[i].stop_video);
      li.setAttribute("id", "slide_" + i);
      if (type == "image") {
        li.style.backgroundImage = "url('" + this.slidesItems[i].url + "')";
      } else {
        // Append content into li
        li.appendChild(slide);
      }
      // Append li into ul list
      this.slides.appendChild(li);
    }
  };

  /**
   * slideShow function to show the current slide according to the time.
   *
   * @param {number} time the current video time
   * @return {void} doesn't return anything
   * @function slideShow
   */
  this.slideShow = function (time) {
    const currentTime = Math.floor(time);
    var videoplayer = document.getElementsByClassName("vjs-tech")[0];

    var keys = Object.keys(this.slidesItems);
    var active = false;
    for (let i = 0; i <= keys.length - 1; i++) {
      //if (currentTime >= this.slidesItems[i].start && currentTime < this.slidesItems[i].end) {
      if (
        currentTime >= this.slidesItems[i].start &&
        (currentTime < this.slidesItems[i].end ||
          (i + 1 < keys.length &&
            this.slidesItems[i + 1].start < this.slidesItems[i].end + 2 &&
            this.slidesItems[i].end + 2 > currentTime))
      ) {
        //* Uncomment (and comment next) to not hide slide if next if at less than 2sec
        if (currentTime <= this.slidesItems[i].end)
          currentSlide = document.getElementById("slide_" + i);
        else if (
          i + 1 < keys.length &&
          currentTime >= this.slidesItems[i + 1].start
        ) {
          document.getElementById("slide_" + i).style.display = "none";
          currentSlide = document.getElementById("slide_" + (i + 1));
          if (
            currentSlide.style.display != "block" &&
            this.slidesItems[i + 1].stop_video == "1"
          ) {
            player.pause();
          }
        }
        //*/
        /* Uncomment (and comment previous) to hide all slide at end
                        currentSlide = document.getElementById('slide_'+i);
                        //*/
        if (
          currentSlide.style.display != "block" &&
          this.slidesItems[i].stop_video == "1"
        ) {
          player.pause();
        }
        currentSlide.style.display = "block";
        active = true;
        player.trigger("changemode", current_slide_mode);
      } else {
        const oldSlide = document.getElementById("slide_" + i);
        oldSlide.style.display = "none";
      }
    }
    if (!active) {
      player.trigger("changemode", no_slide);
    }
    return false;
  };

  /**
   * slideBar function to show position of the slides above the reading bar
   *
   * @return {void} doesn't return anything
   * @function slideBar
   */
  this.slideBar = function () {
    const progressbar = document.getElementsByClassName(
      "vjs-progress-holder",
    )[0];
    // Create the slidebar
    var slidebar = document.createElement("div");
    slidebar.className = "vjs-chapbar";
    var slidebar_holder = document.createElement("div");
    slidebar_holder.className = "vjs-chapbar-holder";
    slidebar.appendChild(slidebar_holder);
    progressbar.appendChild(slidebar);
    // Create slide(s) into the slidebar
    var duration = player.duration();
    var keys = Object.keys(this.slidesItems);
    for (let i = 0; i <= keys.length - 1; i++) {
      var slidebar_left =
        (parseInt(this.slidesItems[i].start) / duration) * 100;
      var slidebar_width =
        (parseInt(this.slidesItems[i].end) / duration) * 100 - slidebar_left;
      var id = this.slidesItems[i].id;
      var type = this.slidesItems[i].type;
      var newslide = document.createElement("div");
      newslide.className = "vjs-chapbar-chap";
      newslide.setAttribute(
        "style",
        "left: " +
          slidebar_left +
          "%; width: " +
          slidebar_width +
          "%; background-color: " +
          slide_color[type],
      );
      newslide.id = "slidebar_" + i;
      slidebar_holder.appendChild(newslide);
    }
  };

  /**
   * slideMode function to change display mode for the slides.
   *
   * @return {void} doesn't return anything
   * @function slideMode
   */
  this.slideMode = function () {
    player.on("changemode", function (e, mode) {
      var videoplayer = document.getElementsByClassName("vjs-tech")[0],
        sclass = mode in slide_mode_list ? mode : "",
        vclass = sclass != "" ? "vjs-tech " + sclass : "vjs-tech";
      if (currentSlide) {
        currentSlide.className = sclass;
      }
      videoplayer.className = vclass;
      document.getElementsByClassName(
        "vjs-slide-manager",
      )[0].firstChild.firstChild.innerHTML = slide_mode_list[mode];
    });
  };

  /**
   * slideButton function create a button on the player to manage slides.
   *
   * @return {void} doesn't return anything
   * @function slideButton
   */
  this.slideButton = function () {
    if (document.getElementsByClassName("vjs-fullscreen-control"))
      // Create the slide view mode
      var vjs_menu_item = videojs.getComponent("MenuItem");
    var SlideMode = videojs.extend(vjs_menu_item, {
      constructor: function (player, options) {
        options = options || {};
        options.label = options.label;
        vjs_menu_item.call(this, player, options);
        this.on("click", this.onClick);
        this.addClass("vjs-slide-mode");
        this.controlText(gettext("Turn to ") + options.mode);
        this.setAttribute("data-mode", options.mode);
      },
      onClick: function () {
        this.setAttribute("aria-checked", true);
        this.addClass("vjs-selected");
        current_slide_mode = this.el().getAttribute("data-mode");
        // console.log("click current_slide_mode: " + current_slide_mode);
        player.trigger("changemode", current_slide_mode);

        var available = document.getElementsByClassName("vjs-slide-mode");
        for (let i = 0, nb = available.length, e; i < nb; i++) {
          //for (let e of available) {
          let e = available[i];
          if (e.firstChild.innerHTML != this.el().firstChild.innerHTML) {
            e.setAttribute("aria-checked", false);
            e.classList.remove("vjs-selected");
          }
        }
      },
    });

    // Create the slide manager menu title
    var SlideTitle = videojs.extend(vjs_menu_item, {
      constructor: function (player, options) {
        options = options || {};
        vjs_menu_item.call(this, player, options);
        this.off("click");
      },
    });

    // Create the slide menu manager
    var vjs_menu_button = videojs.getComponent("MenuButton");
    var SlideButton = videojs.extend(vjs_menu_button, {
      constructor: function (player, options) {
        options = options || {};
        vjs_menu_button.call(this, player, options);
        this.addClass("vjs-slide-manager");
        this.controlText(gettext("Open slide manager"));
        this.el().firstChild.firstChild.innerHTML =
          slide_mode_list[current_slide_mode];
      },
      createItems: function () {
        var items = [];

        items.push(
          new SlideTitle(player, {
            el: videojs.dom.createEl("li", {
              className: "vjs-menu-title vjs-slide-manager-title",
              innerHTML: gettext("Enrich mode"),
            }),
          }),
        );

        for (let e in slide_mode_list) {
          items.push(
            new SlideMode(player, {
              label: slide_mode_list[e],
              mode: e,
            }),
          );
        }

        return items;
      },
    });
    var newbutton = new SlideButton(player);
    if (document.getElementsByClassName("vjs-slide-manager").length > 0) {
      document
        .getElementsByClassName("vjs-slide-manager")[0]
        .parentNode.removeChild(
          document.getElementsByClassName("vjs-slide-manager")[0],
        );
    }
    player.controlBar
      .el()
      .insertBefore(
        newbutton.el(),
        document.getElementsByClassName("vjs-fullscreen-control")[0],
      );
  };
  ////VideoSLide construction (need to be and the end in order to register called methods)
  this.slides = document.createElement("ul");
  this.slidesItems = items;
  this.oldTime = 0;
  this.appendSlider();
  this.slideButton();
  this.slideMode();
  currentSlide = document.getElementById("slide_0");
  player.trigger("changemode", default_slide_mode);
};

const onPlayerReady = function (player, options) {
  try {
    player.addClass("vjs-slides");
  } catch (e) {
    if (player.className.indexOf("vjs-slides") < 0)
      player.className += " vjs-slides";
  }
  var slides = new VideoSlides(options);

  player.on("timeupdate", function () {
    slides.slideShow(this.currentTime());
  });
};

/**
 * A video.js plugin.
 *
 * @function slides
 * @param {object} [options={}]
 * 		  An object of options left to the plugin author to define.
 */
const slides = function (options) {
  this.ready(function () {
    onPlayerReady(this, videojs.mergeOptions(slides_defaults, options));
  });
};

// Register the plugin with video.js.
registerSlidePlugin("slides", slides);
