document.addEventListener("DOMContentLoaded", function () {
  const script = document.getElementById("tr_script");
  const param_url = script.getAttribute("data-url");
  const param_language = script.getAttribute("data-language");

  let player = videojs("podvideoplayer");
  player.ready(function () {
    let lastMod = null;
    setInterval(function () {
      let tracks = player.textTracks();
      for (let i = 0; i < tracks.length; i++) {
        const track = tracks[i];
        if (track.kind === "captions") {
          let current_mod = null;
          fetch(param_url)
            .then((r) => {
              current_mod = r.headers.get("Last-Modified");
              if (lastMod && current_mod && lastMod === current_mod) {
                return;
              }
              lastMod = current_mod;
              let newTrack = player.addRemoteTextTrack(
                {
                  kind: "captions",
                  language: param_language,
                  src: param_url,
                  default: true,
                },
                false
              );

              player.removeRemoteTextTrack(track);

              newTrack.addEventListener("load", (e) => {
                newTrack.mode = "showing";
              });
              // show all tracks
              for (var i = 0; i < tracks.length; i++) {
                if (tracks[i].kind === "captions") {
                  tracks[i].mode = "showing";
                }
              }
            })
            .catch((e) => {
              // console.log(e)
            });
        }
      }
    }, 1000);
  });
});
