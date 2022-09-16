let PlaylistPlayer = {
  invalid_feedback_value: "Please provide a valid value for this field",
  invalid_feedback_password: "The password is incorrect.",
  getParameters: function () {
    let parameters = "";
    if (this.auto_on) {
      parameters += "&auto=on";
    }
    if (this.loop_on) {
      parameters += "&loop=on";
    }
    if (this.is_iframe) {
      parameters += "&is_iframe=true";
    }
    return parameters;
  },

  unselectCurrent: function () {
    $(this.elements[this.current_position - 1])
      .parent()
      .removeClass("on");
  },
  setCurrent: function (position) {
    this.current_position = position;
    $(this.elements[this.current_position - 1])
      .parent()
      .addClass("on");
    const vtitle = $(this.elements[this.current_position - 1]).data("title"),
      purl =
        "/playlist/" + this.playlist + "/?p=" + position + this.getParameters();
    history.pushState({ title: vtitle }, "", purl);
    for (let c in this.titlectns) {
      this.titlectns[c].innerHTML = vtitle;
    }
  },
  onPlayerEnd: function () {
    const _this = this;
    if (this.current_position != this.length || this.loop_on) {
      if (this.current_position != this.length) {
        this.loadVideo(this.current_position + 1);
      } else if (this.loop_on) {
        this.loadVideo(1);
      }
    }
  },

  loadVideo: function (position) {
    this.unselectCurrent();
    const video_url = this.elements[position - 1].children[1].children[0].href,
      ajax_url = video_url.replace("/video/", "/video/xhr/"),
      parameters =
        ajax_url.indexOf("?") > 0
          ? this.getParameters()
          : this.getParameters().replace(/^&/, "?"),
      //, password = $(this.current_element).parent().children('.vdata').data('password') == 'unchecked'
      _this = this;
    $.ajax({
      url: ajax_url + parameters,
      context: document.body,
      dataType: "json",
    }).done(function (json) {
      if (json.status == "ok") {
        _this.setPlayer(json);
        $("#info-video").html(json.html_video_info);
        // Update aside (Enrichement info, Managment links, Notes)
        if (!_this.is_iframe) {
          // Show / Hide enrichment info block
          if (json.version == "E")
            $("#card-enrichmentinformations").removeClass("off");
          else $("#card-enrichmentinformations").addClass("off");
          // Update managment links
          $("#card-managevideo .card-body a").each(function () {
            $(this).attr(
              "href",
              $(this)
                .attr("href")
                .replace(/(.*)\/([^/]*)\/([^/])*$/, function (str, g0, g1, g2) {
                  return g0 + "/" + json.slug + "/" + (g2 ? g2 : "");
                })
            );
          });
          // Update note form
          $("#card-takenote").html(json.html_video_note);
        }
        _this.setCurrent(position);
      } else if (json.error == "password") {
        //Acces restrict by password => Display video password form
        if ($("#video-form-wrapper").length == 0) {
          _this.formctn.append('<div id="video-form-wrapper"></div>');
        }
        $("#video-form-wrapper").removeClass("hidden");
        $("#video-form-wrapper").html(json.html_content);
        $("#video-form-wrapper .invalid-feedback").hide();
        $('#video-form-wrapper button[type="submit"]').click(function (e) {
          e.preventDefault();
          e.stopPropagation();
          const password = $("#id_password").val(),
            csrfmiddlewaretoken = $(
              '#video_password_form > input[name="csrfmiddlewaretoken"]'
            )
              .first()
              .val();
          if (password == "") {
            $("#video-form-wrapper .invalid-feedback")
              .html(this.strings.invalid_feedback_value.replace("'", "'"))
              .show();
            return;
          }
          $.ajax({
            type: "POST",
            data: {
              password: password,
              csrfmiddlewaretoken: csrfmiddlewaretoken,
            },
            url: ajax_url,
            context: document.body,
            dataType: "json",
          }).done(function (json) {
            if (json.status == "ok") {
              $("#video-form-wrapper").empty().addClass("hidden");
              _this.setPlayer(json);
              $("#info-video").html(json.html_video_info);
              _this.setCurrent(position);
            } else {
              $("#video-form-wrapper .invalid-feedback")
                .html(this.strings.invalid_feedback_password)
                .show();
            }
          });
        });
      } else if (json.error == "access") {
        rurl = json.url + "?";
        if (_this.is_iframe) {
          rurl += "is_iframe=true&";
        }
        rurl +=
          "referrer=" +
          _this.baseurl +
          "/playlist/" +
          _this.slug +
          "/?p=" +
          position +
          _this.getParameters().replace(/&/g, "%26");
        window.location.href = rurl;
      } else if (json.error == "deny") {
        //User is authenticate but not allowed => Go next (TODO... actualy just reload page)
        const nposition = position < _this.elements.length ? position + 1 : 1;
        _this.loadVideo(nposition);
      }
    });
  },
  init: function (o) {
    /* o is a javascript object containing playlist parameters for playlist player initialisation and playing :
     *  - version : String ('O' or 'E') corresponding to the default version of the video in wich it should be played
     *  - current_position : Number equals to the position of the current video (can be pass has query string ex: p=1)
     *  - length : Number of video in the playlist
     *  - elements : List of HTML playlist video elements
     *  - baseurl : String equals to pod site base url
     *  - is_iframe : Boolean to define if the playlist must be show in iframe mode or not
     *  - is_360 : Boolean to specifiy if the current video is a 360° video
     *  - vsjLogo : Logo to add to the player (can be null)
     *  - formctn : HTML element for a eventualy needed form
     *  - vtitlectn : List of HTML element where the current video title is display (and should be update)
     *  - head_files : Object containning a List of js and css that could be load or unload for any video type (enrichments, 360°, etc)
     *  - controls : Object containing loop and auto controls HTML elements
     *  - strings : Object containing pre-translated strings that could be needed to display (Cf info or alert messages)
     */
    this.version = o.version;
    this.current_position = o.current_position;
    this.length = o.length;
    this.baseurl = o.baseurl;
    this.slug = o.slug;
    this.is_iframe = o.is_iframe;
    this.is_360 = o.is_360;
    this.vjsLogo = o.vjsLogo;
    this.formctn = o.formctn;
    this.titlectns = o.vtitlectns;
    this.headFiles.set(o.head_files);
    this.controls = o.controls;
    this.strings = o.strings ? o.strings : this.strings;
    this.auto_on = this.loop_on = false;
    this.elements = [];
    this.hasPlayed = false;

    const parameter = [
      /(playlist)\/([^/]+)\//,
      /(auto)\=([^&]+)/,
      /(loop)\=([^&]+)/,
    ];
    this.playlist = window.location.href.match(parameter[0])[2];
    let _this = this;

    if (window.location.href.match(parameter[1])) {
      $(this.controls.auto).addClass("on");
      this.auto_on = true;
    }
    if (window.location.href.match(parameter[2])) {
      $(this.controls.loop).addClass("on");
      this.loop_on = true;
    }

    function toogleOption(e) {
      e.preventDefault();
      e.stopPropagation();
      if ($(this).hasClass("on")) {
        $(this).removeClass("on");
        _this[$(this).data("id") + "_on"] = false;
      } else {
        $(this).addClass("on");
        _this[$(this).data("id") + "_on"] = true;
      }
    }

    for (let c in this.controls) {
      $(this.controls[c]).data("id", c);
      this.controls[c].onclick = toogleOption;
    }

    for (let i = 0, p = 1, nbe = o.elements.length; i < nbe; i++, p++) {
      _this.elements.push(o.elements[i]);
      $(o.elements[i])
        .find("a")
        .data("position", p)
        .on("click", function (e) {
          if ($(this).data("position") == _this.current_position) {
            e.preventDefault(); //e.stopPropagation();
            player.play();
          } /*if(_this.auto_on)*/ else {
            e.preventDefault(); //e.stopPropagation();
            _this.loadVideo($(this).data("position"));
          }
        });
    }
    player.on("ended", function () {
      _this.onPlayerEnd();
    });
    // console.log('Should load video '+this.current_position)
    this.loadVideo(this.current_position);
  },
  headFiles: {
    plugins: {
      enrichment: null,
      chapter: null,
      vr360: null,
      overlay: null,
      overview: null,
    },
    set: function (o) {
      for (let p in o) {
        if (this.plugins.hasOwnProperty(p)) {
          this.plugins[p] = o[p];
        }
      }
    },
    getOrLoad: function (p, cb) {
      if (this.plugins[p].js) {
        if ($("#" + p + "_style_id").length == 0) {
          $("head").append(
            '<link id="' +
              p +
              '_style_id" href="' +
              this.plugins[p].css +
              '" rel="stylesheet" />'
          );
        }
        if ($("#" + p + "_script_id").length == 0) {
          let s = document.createElement("SCRIPT");
          s.id = p + "_script_id";
          s.src = this.plugins[p].js;
          if (typeof cb === "function") {
            s.onload = cb;
          }
          document.getElementsByTagName("HEAD")[0].append(s);
        } else if (typeof cb == "function") {
          cb();
        }
      }
    },
    unload: function (p) {
      $("#" + p + "_style_id, #" + p + "_script_id").remove();
    },
    unloadCSS: function (p) {
      $("#" + p + "_style_id").remove();
    },
  },

  setPlayer: function (json) {
    // Register player settings
    const volume = player.volume(),
      muted = player.muted();

    // Remove some overlay or enrichment element wich could cause problems if not need
    const has_overlay = json.overlay && json.overlay.length > 0,
      has_enrichment = json.version != "O";
    if (!has_enrichment) {
      this.headFiles.unloadCSS("enrichment");
      metadataTrack = null;
    }
    if (!has_overlay) {
      this.headFiles.unloadCSS("overlay");
    }

    // Replace video_element
    $(
      "form#video_count_form, ul.video-slides, ul#overlays, div.chapters-list"
    ).remove();
    player.dispose();
    $("#info-video-wrapper, #info-video").eq(0).before(json.html_video_element);

    const _this = this;

    player = videojs("podvideoplayer", options, function () {});
    player.ready(function () {
      // Chapters
      if (json.chapter.length > 0) {
        player.videoJsChapters();
        $(".vjs-big-play-button").css("z-index", 2);
        $(".vjs-control-bar").css("z-index", 3);
      }

      // Enrichments
      if (has_enrichment) {
        $(player.el().getElementsByTagName("VIDEO")[0]).append(
          '<track kind="metadata" src="' +
            json.enrichtracksrc +
            '" label="enrichment" />'
        );
        _this.headFiles.getOrLoad("enrichment", function () {
          var tracks = player.el().getElementsByTagName("TRACK");
          for (var i = 0; i < tracks.length; i++) {
            if (
              tracks[i].kind === "metadata" &&
              tracks[i].label === "enrichment"
            ) {
              metadataTrack = tracks[i];
              metadataTrack.index = i;
              break;
            }
          }
          player.on("loadedmetadata", function () {
            let slide = [],
              player = this;
            if (!metadataTrack.cues) {
              //Safari do not get cues
              let tracksrc = player.el().getElementsByTagName("TRACK")[
                metadataTrack.index
              ].src;
              loadEnrichmentVTTfile(tracksrc, function (cues) {
                if (typeof player.slides === "function") {
                  player.slides(cues);
                }
              });
            } else {
              for (i = 0; i < metadataTrack.cues.length; i++) {
                // Replace tabs by spaces to prevent a "JSON.parse: bad control character in string literal" error.
                data = JSON.parse(
                  metadataTrack.cues[i].text.replace(/\t/g, " ")
                );
                slide.push({
                  title: data.title,
                  url: data.url,
                  type: data.type,
                  stop_video: data.stop_video,
                  start: metadataTrack.cues[i].startTime,
                  end: metadataTrack.cues[i].endTime,
                });
              }
              if (typeof player.slides === "function") {
                try {
                  player.slides(slide);
                } catch (e) {}
              }
            }
          });
        });
      }

      // Overlays
      if (has_overlay) {
        _this.headFiles.getOrLoad("overlay", function () {
          player.on("loadedmetadata", function () {
            if (typeof player.overlay === "function") {
              player.overlay({ overlays: json.overlay });
            }
          });
        });
      }

      // Add vttThumbnails
      if (json.overview) {
        if (typeof player.vttThumbnails === "function") {
          player.vttThumbnails({ src: _this.baseurl + json.overview });
        } else {
          _this.headFiles.getOrLoad("overview", function () {
            try {
              player.vttThumbnails({ src: _this.baseurl + json.overview });
            } catch (e) {
              console.warn("Error in retrieving overview image : " + e);
            }
          });
        }
      }

      // Add 360° video
      if (json.is_360) {
        if (typeof player.vr === "function") {
          player.vr({ projection: "360" });
        } else {
          _this.headFiles.getOrLoad("vr360", function () {
            try {
              player.vr({ projection: "360" });
            } catch (e) {
              console.warn("Error in calling video 360° function : " + e);
            }
          });
        }
      }

      // Add info and playlist controls and resize player if is_iframe
      if (_this.is_iframe) {
        player.videoJsInfo();
        player.videoJsPlaylist();
        if (typeof resizeVideoJs === "function") {
          resizeVideoJs();
        }
        if (typeof setOnPlayerPlayPause === "function") {
          setOnPlayerPlayPause();
        }
        if (!_this.hasPlayed) {
          player.on("firstplay", function () {
            $("#card-playlist .close.hidden").removeClass("hidden");
            _this.hasPlayed = true;
          });
        }
      }

      // Set video source
      if (json.is_video) {
        if (json.src.m3u8) {
          player.src(json.src.m3u8);
          player.hlsQualitySelector({
            displayCurrentQuality: true,
          });
          player.on("error", function (e) {
            e.stopImmediatePropagation();
            var error = player.error();
            //alert(error.code+" "+error.type+" "+error.message);
            if (error.code == 3 || error.code == 4) {
              //console.log('error!', error.code, error.type , error.message);
              if (player.src() == "" || player.src().indexOf("m3u8") != -1) {
                player.src(json.src.mp4);
                player.controlBar.addChild("QualitySelector");
                if (_this.hasPlayed) player.play();
              }
            }
          });
        } else {
          player.src(json.src.mp4);
          player.controlBar.addChild("QualitySelector");
        }
      } else if (json.src.m4a) player.src(json.src.m4a);

      // Add videojs logo if defined
      if (_this.vjsLogo) player.videoJsLogo(_this.vjsLogo);

      // Add viewCount
      player.on("firstplay", function () {
        var data_form = $("#video_count_form").serializeArray();
        jqxhr = $.post($("#video_count_form").attr("action"), data_form);
      });

      // add onPlayerEnd listener for the rebuild player
      player.on("ended", function () {
        _this.onPlayerEnd();
      });

      // Restore registered settings
      player.volume(volume);
      player.muted(muted);

      // Play if auto is active
      if (_this.auto_on) player.play();
    });
  },
};
