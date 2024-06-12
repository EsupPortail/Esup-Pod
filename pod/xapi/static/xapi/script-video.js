/**
 * Esup-Pod Xapi video scripts.
 */

// Read-only globals defined in video-script.html
/*
global player
*/

// Read-only globals defined in xapi/script.js
/*
global createStatement sendStatement
*/

// Read-only globals defined in xapi_video.html
/*
global progress
*/

const __XAPI_VIDEO_VERBS__ = {
  initialized: "http://adlnet.gov/expapi/verbs/initialized",
  played: "https://w3id.org/xapi/video/verbs/played",
  paused: "https://w3id.org/xapi/video/verbs/paused",
  seeked: "https://w3id.org/xapi/video/verbs/seeked",
  interacted: "http://adlnet.gov/expapi/verbs/interacted",
  completed: "http://adlnet.gov/expapi/verbs/completed",
  terminated: "http://adlnet.gov/expapi/verbs/terminated",
};

const __XAPI_VIDEO_CONTEXT_EXTENSIONS__ = {
  "session-id": "https://w3id.org/xapi/video/extensions/session-id",
  "cc-subtitle-enabled":
    "https://w3id.org/xapi/video/extensions/cc-subtitle-enabled",
  "cc-subtitle-lang": "https://w3id.org/xapi/video/extensions/cc-subtitle-lang",
  "frame-rate": "https://w3id.org/xapi/video/extensions/frame-rate",
  "full-screen": "https://w3id.org/xapi/video/extensions/full-screen",
  quality: "https://w3id.org/xapi/video/extensions/quality",
  "screen-size": "https://w3id.org/xapi/video/extensions/screen-size",
  "video-playback-size":
    "https://w3id.org/xapi/video/extensions/video-playback-size",
  speed: "https://w3id.org/xapi/video/extensions/speed",
  track: "https://w3id.org/xapi/video/extensions/track",
  "user-agent": "https://w3id.org/xapi/video/extensions/user-age",
  volume: "https://w3id.org/xapi/video/extensions/volume",
  length: "https://w3id.org/xapi/video/extensions/length",
  "completion-threshold":
    "https://w3id.org/xapi/video/extensions/completion-threshold",
};

const __XAPI_VIDEO_RESULT_EXTENSIONS__ = {
  // score, completion (only for completed statement), duration
  time: "https://w3id.org/xapi/video/extensions/time",
  "time-from": "https://w3id.org/xapi/video/extensions/time-from",
  "time-to": "https://w3id.org/xapi/video/extensions/time-to",
  progress: "https://w3id.org/xapi/video/extensions/progress",
  "played-segments": "https://w3id.org/xapi/video/extensions/played-segments",
};

var last_time = [];
const played_segments = [];
var time_played = 0;
var time_paused = 0;
var time_seek = 0;

player.on("timeupdate", function () {
  progress[parseInt(player.currentTime(), 10)] = 1;
  if (progress.length == parseInt(player.duration(), 10)) {
    set_completed_statement();
    active_statement();
  }
  last_time.push(player.currentTime().toFixed(3));
  last_time = last_time.slice(-10); // we keep only the 10 last values
});

player.on("play", function () {
  action = "played";
  verb = {
    id: __XAPI_VIDEO_VERBS__[action],
    display: { "en-US": action },
  };
  time_played = player.currentTime().toFixed(3);
  result = {
    extensions: {
      "https://w3id.org/xapi/video/extensions/time": time_played,
    },
  };
  if (registration_xapi == "") registration_xapi = create_UUID();
  context = {
    contextActivities: {
      category: [
        {
          id: "https://w3id.org/xapi/video",
        },
      ],
    },
    extensions: {
      "https://w3id.org/xapi/video/extensions/session-id": session_id,
      "https://w3id.org/xapi/video/extensions/length": player
        .duration()
        .toFixed(3),
    },
    registration: registration_xapi,
  };
  active_statement();
});

player.on("pause", function () {
  action = "paused";
  verb = {
    id: __XAPI_VIDEO_VERBS__[action],
    display: { "en-US": action },
  };
  time_paused = player.currentTime().toFixed(3);
  result = {
    extensions: {
      "https://w3id.org/xapi/video/extensions/time": time_paused,
      "https://w3id.org/xapi/video/extensions/played-segments":
        time_played + "[.]" + time_paused,
      "https://w3id.org/xapi/video/extensions/progress": (
        progress.length / player.duration()
      ).toFixed(3),
    },
  };
  played_segments.push(time_played + "[.]" + time_paused);
  if (registration_xapi == "") registration_xapi = create_UUID();
  context = {
    contextActivities: {
      category: [
        {
          id: "https://w3id.org/xapi/video",
        },
      ],
    },
    extensions: {
      "https://w3id.org/xapi/video/extensions/session-id": session_id,
      "https://w3id.org/xapi/video/extensions/length": player
        .duration()
        .toFixed(3),
    },
    registration: registration_xapi,
  };
  active_statement();
});

player.on("seeked", function () {
  time_seek = player.currentTime().toFixed(3);
  action = "seeked";
  verb = {
    id: __XAPI_VIDEO_VERBS__[action],
    display: { "en-US": action },
  };
  result = {
    extensions: {
      "https://w3id.org/xapi/video/extensions/time-to": time_seek,
      "https://w3id.org/xapi/video/extensions/time-from":
        last_time[last_time.indexOf(time_seek) - 1],
    },
  };
  if (registration_xapi == "") registration_xapi = create_UUID();
  context = {
    contextActivities: {
      category: [
        {
          id: "https://w3id.org/xapi/video",
        },
      ],
    },
    extensions: {
      "https://w3id.org/xapi/video/extensions/session-id": session_id,
    },
    registration: registration_xapi,
  };
  active_statement();
});

player.on("ended", function () {
  action = "terminated";
  verb = {
    id: __XAPI_VIDEO_VERBS__[action],
    display: { "en-US": action },
  };
  result = {
    completion: true,
    extensions: {
      "https://w3id.org/xapi/video/extensions/played-segments":
        played_segments.join("[,]"),
      "https://w3id.org/xapi/video/extensions/progress": (
        progress.length / player.duration()
      ).toFixed(3),
      "https://w3id.org/xapi/video/extensions/time": player
        .currentTime()
        .toFixed(3),
    },
  };
  if (registration_xapi == "") registration_xapi = create_UUID();
  context = {
    contextActivities: {
      category: [
        {
          id: "https://w3id.org/xapi/video",
        },
      ],
    },
    extensions: {
      "https://w3id.org/xapi/video/extensions/session-id": session_id,
      "https://w3id.org/xapi/video/extensions/length": player
        .duration()
        .toFixed(3),
      "https://w3id.org/xapi/video/extensions/completion-threshold": (
        parseInt(player.duration(), 10) / player.duration()
      ).toFixed(3),
    },
    registration: registration_xapi,
  };
  active_statement();
});

player.on("ratechange", function () {
  set_interacted_statement();
  active_statement();
});
player.on("fullscreenchange", function () {
  set_interacted_statement();
  active_statement();
});
player.on("volumechange", function () {
  set_interacted_statement();
  active_statement();
});
player.on("texttrackchange", function () {
  set_interacted_statement();
  active_statement();
});
player.on("resize", function () {
  set_interacted_statement();
  active_statement();
});

player.on("loadedmetadata", function () {
  action = "initialized";
  verb = {
    id: __XAPI_VIDEO_VERBS__[action],
    display: { "en-US": action },
  };
  result = {};
  if (registration_xapi == "") registration_xapi = create_UUID();
  cc_lang = get_current_subtitle_lang();
  current_quality = get_current_quality();
  context = {
    contextActivities: {
      category: [
        {
          id: "https://w3id.org/xapi/video",
        },
      ],
    },
    extensions: {
      "https://w3id.org/xapi/video/extensions/volume": player.volume(),
      "https://w3id.org/xapi/video/extensions/video-playback-size":
        player.currentWidth() + "x" + player.currentHeight(),
      "https://w3id.org/xapi/video/extensions/user-agent":
        window.navigator.userAgent,
      "https://w3id.org/xapi/video/extensions/speed": player.playbackRate(),
      "https://w3id.org/xapi/video/extensions/completion-threshold": (
        parseInt(player.duration(), 10) / player.duration()
      ).toFixed(3),
      "https://w3id.org/xapi/video/extensions/session-id": session_id,
      "https://w3id.org/xapi/video/extensions/length": player
        .duration()
        .toFixed(3),
      "https://w3id.org/xapi/video/extensions/quality":
        current_quality.width + "x" + current_quality.height,
      "https://w3id.org/xapi/video/extensions/screen-size":
        screen.width + "x" + screen.height,
      "https://w3id.org/xapi/video/extensions/frame-rate":
        current_quality.frameRate,
      "https://w3id.org/xapi/video/extensions/cc-enabled": cc_lang != "",
      "https://w3id.org/xapi/video/extensions/cc-subtitle-lang": cc_lang,
      "https://w3id.org/xapi/video/extensions/full-screen":
        player.isFullscreen(),
    },
    registration: registration_xapi,
  };
  result = {};
  active_statement();
});

function set_completed_statement() {
  action = "completed";
  verb = {
    id: __XAPI_VIDEO_VERBS__[action],
    display: { "en-US": action },
  };
  result = {
    completion: true,
    extensions: {
      "https://w3id.org/xapi/video/extensions/played-segments":
        played_segments.join("[,]"),
      "https://w3id.org/xapi/video/extensions/progress": (
        progress.length / player.duration()
      ).toFixed(3),
      "https://w3id.org/xapi/video/extensions/time": player
        .currentTime()
        .toFixed(3),
    },
  };
  context = {
    contextActivities: {
      category: [
        {
          id: "https://w3id.org/xapi/video",
        },
      ],
    },
    extensions: {
      "https://w3id.org/xapi/video/extensions/completion-threshold": (
        parseInt(player.duration(), 10) / player.duration()
      ).toFixed(3),
      "https://w3id.org/xapi/video/extensions/session-id": session_id,
      "https://w3id.org/xapi/video/extensions/length": player
        .duration()
        .toFixed(3),
    },
    registration: registration_xapi,
  };
}

function set_interacted_statement() {
  action = "interacted";
  verb = {
    id: __XAPI_VIDEO_VERBS__[action],
    display: { "en-US": action },
  };
  result = {
    extensions: {
      "https://w3id.org/xapi/video/extensions/time": player
        .currentTime()
        .toFixed(3),
    },
  };
  if (registration_xapi == "") registration_xapi = create_UUID();
  cc_lang = get_current_subtitle_lang();
  current_quality = get_current_quality();
  quality = "";
  framerate = "";
  if (current_quality) {
    quality = current_quality.width + "x" + current_quality.height;
    framerate = current_quality.frameRate;
  }
  context = {
    contextActivities: {
      category: [
        {
          id: "https://w3id.org/xapi/video",
        },
      ],
    },
    extensions: {
      "https://w3id.org/xapi/video/extensions/volume": player.volume(),
      "https://w3id.org/xapi/video/extensions/video-playback-size":
        player.currentWidth() + "x" + player.currentHeight(),
      "https://w3id.org/xapi/video/extensions/user-agent":
        window.navigator.userAgent,
      "https://w3id.org/xapi/video/extensions/speed": player.playbackRate(),
      "https://w3id.org/xapi/video/extensions/completion-threshold": (
        parseInt(player.duration(), 10) / player.duration()
      ).toFixed(3),
      "https://w3id.org/xapi/video/extensions/session-id": session_id,
      "https://w3id.org/xapi/video/extensions/length": player
        .duration()
        .toFixed(3),
      "https://w3id.org/xapi/video/extensions/quality": quality,
      "https://w3id.org/xapi/video/extensions/screen-size":
        screen.width + "x" + screen.height,
      "https://w3id.org/xapi/video/extensions/frame-rate": framerate,
      "https://w3id.org/xapi/video/extensions/cc-enabled": cc_lang != "",
      "https://w3id.org/xapi/video/extensions/cc-subtitle-lang": cc_lang,
      "https://w3id.org/xapi/video/extensions/full-screen":
        player.isFullscreen(),
    },
    registration: registration_xapi,
  };
}

function get_current_subtitle_lang() {
  let textTracks = player.textTracks();
  let lang = "";
  for (let i = 0; i < textTracks.length; i++) {
    if (textTracks[i].kind == "subtitles" && textTracks[i].mode == "showing") {
      lang = textTracks[i].language;
    }
  }
  return lang;
}

function get_current_quality() {
  let qualitys = player.qualityLevels();
  if (qualitys.length > 0) return qualitys[qualitys.selectedIndex];
}

function active_statement() {
  timestamp = new Date().toISOString();
  let stmt = createStatement();
  sendStatement(stmt);
}
