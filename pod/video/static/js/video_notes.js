document.addEventListener("submit", function (e) {
  const podvideo = document.getElementById("podvideoplayer");
  /**
   * Put player in pause when displaying the form to create a note
   */
  if (e.target.classList.contains("add_video_notes_form")) {
    podvideo.player.pause();
  }

  if (e.target.getAttribute("id") == "video_notes_form") {
    /**
     * Include player timestamp when editing a note
     */
    const id_timestamp = document.getElementById("id_timestamp");
    // On a comment, there is no id_timestamp.
    if (id_timestamp) {
      if (!id_timestamp.value) {
        id_timestamp.value = Math.floor(podvideo.player.currentTime());
      }
    }
    pod_note_submit(e);
  } else if (
    e.target.matches("div.mgtNotes form, div.mgtNote form, div.mgtComment form")
  ) {
    pod_note_submit(e);
  }
});

/**
 * Add a visual indent on 3 first levels of comments
 */
function pod_note_comment_offset() {
  let divComments = document.querySelectorAll("#id_notes div.comments");
  for (var i = 0; i < Math.min(divComments.length, 3); i++) {
    divComments[i].classList.add("ms-3");
  }
}

/**
 * Handle every pod-note submission (except download)
 */
var pod_note_submit = function (e) {
  if (!e.target.classList.contains("download_video_notes_form")) {
    e.preventDefault();
    send_form_data_vanilla(
      e.target.getAttribute("action"),
      "display_notes_place",
      e.target,
    );
  }
};

/**
 * Fill allocated space for notes and comments with content
 */
var display_notes_place = function (data) {
  document.getElementById("card-takenote").innerHTML = data;

  if (document.getElementById("video_notes_form"))
    document.getElementById("video_notes_form").scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  TriggerAlertClose();
  pod_note_comment_offset();
};

/*
 * Manage all clicks events
 */
document.addEventListener(
  "click",
  function (event) {
    const podvideo = document.getElementById("podvideoplayer");

    if (event.target.matches("span.timestamp")) {
      /**
       * Set the current time of the player to the timestamp of the note
       */
      let timestamp = event.target.dataset.start;
      if (!isNaN(Number(timestamp))) {
        // console.log("Moving player to " + timestamp);
        podvideo.player.currentTime(timestamp);
      }
    } else if (
      event.target.matches(".js-note-toggle") ||
      event.target.parentNode.matches(".js-note-toggle")
    ) {
      /**
       * Handle click on note header to toggle partial or full display
       */
      if (event.target.matches(".js-note-toggle")) {
        form_data = event.target.parentNode;
      } else {
        form_data = event.target.parentNode.parentNode;
      }
      send_form_data_vanilla(
        form_data.getAttribute("action"),
        "display_notes_place",
        form_data,
      );
    } else if (
      event.target.matches(".js-comment-toggle") ||
      event.target.parentNode.matches(".js-comment-toggle")
    ) {
      /**
       * Handle click on comment header to toggle partial or full display
       */
      if (event.target.matches(".js-comment-toggle")) {
        form_data = event.target.parentNode.querySelector(
          ".view_video_note_coms_form",
        );
      } else {
        form_data = event.target.parentNode.parentNode.querySelector(
          ".view_video_note_coms_form",
        );
      }
      send_form_data_vanilla(
        form_data.getAttribute("action"),
        "display_notes_place",
        form_data,
      );
    } else if (
      document.getElementById("video_notes_form") &&
      !document.getElementById("video_notes_form").contains(event.target) &&
      !podvideo.contains(event.target) &&
      !("timestamp" in event.target.classList) &&
      !("download_video_notes_form" in event.target.classList)
    ) {
      /**
       * Manage hiding create note or comment form on click on document
       */
      let video_notes_parent =
        document.getElementById("video_notes_form").parentNode;
      let data_form;

      if (video_notes_parent.querySelector(".view_video_notes_form.d-none")) {
        data_form = video_notes_parent.querySelector(
          ".view_video_notes_form.d-none",
        );
      } else {
        data_form = video_notes_parent.querySelector(
          ".view_video_note_coms_form.d-none",
        );
      }
      send_form_data_vanilla(
        data_form.getAttribute("action"),
        "display_notes_place",
        data_form,
      );
    } else if (event.target.matches("#cancel_save")) {
      let data_form = document
        .getElementById("video_notes_form")
        .parentNode.querySelector(".view_video_notes_form.d-none");
      send_form_data_vanilla(
        data_form.getAttribute("action"),
        "display_notes_place",
        data_form,
      );
    } else if (event.target.matches("#cancel_save_com")) {
      let data_form = document
        .getElementById("video_notes_form")
        .parentNode.querySelector(".view_video_note_coms_form.d-none");
      send_form_data_vanilla(
        data_form.getAttribute("action"),
        "display_notes_place",
        data_form,
      );
    }
  },
  false,
);
