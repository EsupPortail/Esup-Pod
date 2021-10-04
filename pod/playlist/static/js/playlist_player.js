let PlaylistPlayer = {
  staticdir: null,
  invalid_feedback_value: "Please provide a valid value for this field",
  invalid_feedback_password: "The password is incorrect.",
  onPlayerEnd: function () {
    let _this = this;
    let parameters = "";
    if (this.auto_on) {
      parameters = parameters + "&auto=on";
    }
    if (this.loop_on) {
      parameters = parameters + "&loop=on";
    }
    if (this.is_iframe) {
      parameters = parameters + "&is_iframe=true";
    }
    if (this.current_position != this.length || this.loop_on) {
      $(this.current_element).parent().removeClass("on");
      $(this.current_element)
        .parent()
        .children(".vdata")
        .text(this.current_position);
      if (this.current_position != this.length) {
        this.current_position++;
        this.current_element = $(".playlist-videos div.row > div > div.card")[
          this.current_position - 1
        ];
      } else if (this.loop_on) {
        this.current_position = 1;
        this.current_element = $(
          ".playlist-videos div.row > div > div.card"
        )[0];
      }
      let current_url = this.current_element.children[1].children[0].href,
        //, password = $(this.current_element).parent().children('.vdata').data('password') == 'unchecked'
        ajax_url = current_url.replace("/video/", "/video_xhr/");
      $.ajax({
        url: ajax_url + parameters,
        context: document.body,
        dataType: "json",
      }).done(function (json) {
        if (json.status == "ok") {
          _this.setPlayer(json);
          $("#info-video").html(json.html_video_info);
        } else if (json.error == "password") {
          //Acces restrict by password => Display video password form
          if ($("#video-form-wrapper").length == 0) {
            _this.formctn.append(
              '<div id="video-form-wrapper" class="jumbotron"></div>'
            );
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
              } else {
                $("#video-form-wrapper .invalid-feedback")
                  .html(this.strings.invalid_feedback_password)
                  .show();
              }
            });
          });
        } else if (json.error == "access") {
          //Acces restrict by authentication => Redirect to loggin page
          window.location.href = json.url;
        } else if (json.error == "deny") {
          //User is authenticate but not allowed => Go next (TODO... actualy just reload page)
          window.location.href = current_url;
        }
      });
    }
  },
  init: function (o) {
    this.staticdir = o.static;
    this.version = o.version;
    this.current_element = o.current_element;
    this.current_position = o.current_position;
    this.length = o.length;
    this.baseurl = o.baseurl;
    this.is_iframe = o.is_iframe;
    this.is_360 = o.is_360;
    this.vjsLogo = o.vjsLogo;
    this.formctn = o.formctn;
    this.headFiles.set(o.head_files);
    this.controls = o.controls;
    this.strings = o.strings ? o.strings : this.strings;
    this.chevron_up = $(this.current_element)
      .parent()
      .children(".vdata")
      .html();
    this.auto_on = this.loop_on = false;

    const parameter = [
        /(playlist)\=([^&]+)/,
        /(auto)\=([^&]+)/,
        /(loop)\=([^&]+)/,
      ],
      playlist = window.location.href.match(parameter[0])[2];
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

    player.on("ended", function () {
      _this.onPlayerEnd();
    });
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
              console.error("Error in retrieving overview image : " + e);
            }
          });
        }
      }

      // Add 360° video
      if(json.is_360) {
        if(typeof player.vttThumbnails === 'function') {
          player.vr({projection: '360'});
        } else {
          _this.headFiles.getOrLoad('overview', function() {
            try {
              player.vr({projection: '360'});
            } catch(e) { console.error('Error in calling video 360° function : '+e) }
          })
        }
      }

      // Add info and playlist controls and resize player if is_iframe
      if (_this.is_iframe) {
        player.videoJsInfo();
        player.videoJsPlaylist();
        if (typeof resizeVideoJs === "function") {
          resizeVideoJs();
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
                player.play();
              }
            }
          });
        } else {
          player.src(json.src.mp4);
          player.controlBar.addChild("QualitySelector");
        }
      } else if (json.src.m4a) player.src(json.src.m4a);
      console.log("SetPlayer src " + player.src());

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

      // Update current_element stylesheet
      $(_this.current_element).parent().addClass("on");
      $(_this.current_element)
        .parent()
        .children(".vdata")
        .html(_this.chevron_up);
      let current_url = _this.current_element.children[1].children[0].href;
      history.pushState(
        {
          title: $(_this.current_element)
            .parent()
            .children(".vdata")
            .data("info"),
        },
        "",
        current_url
      );

      // Restore registered settings
      player.volume(volume);
      player.muted(muted);

      // Play if auto is active
      if (_this.auto_on) player.play();
    });
  },
};
