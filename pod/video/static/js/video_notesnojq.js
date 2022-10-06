/**
 * Handle enter key pressed while editing note or comment
 */
document.addEventListener(
  "keydown",
  "textarea#id_note, textarea#id_comment",
  function (e) {
    if (e.key == "Enter") {
      e.preventDefault();
      if (this.id == "id_note")
        !document.getElementById("id_timestamp").value
          ? document.getElementById("id_timestamp").value = 
              Math.floor(document.getElementById("podvideoplayer").player.currentTime())
            
          : undefined;
      document.getElementById("video_notes_form").submit();
    }
  }
);

document.addEventListener("click",  (e) => {
  if (!e.target.matches("#video_notes_form_save")) return;
  let timestamp = document.getElementById("id_timestamp");
  !timestamp.value
    ? timestamp.value = 
        Math.floor(document.getElementById("podvideoplayer").player.currentTime())
      
    : undefined;
  document.getElementById("video_notes_form").submit();
});

/**
 * Handle click on buttons in three dots menu
 */
document.addEventListener(
  "submit",

   (e) => {
    if (!e.target.matches("#video_notes_form")
      && !e.target.matches("div.mgtNotes form")
      && !e.target.matches("div.mgtNote form")
      && !e.target.matches("div.mgtComment form")
    ) return;
    e.preventDefault();
    if (!e.target.getAttribute("class").includes("download_video_notes_form")) {
      e.preventDefault();
      let data_form = new FormData(e.target)
      send_form_data(
        e.target.getAttribute("action"),
        data_form,
        "display_notes_place",
        "post"
      );
    }
  }
);

/**
 * Fill allocated space for notes and comments with content
 */
var display_notes_place = function (data) {
  document.querySelector("div#card-takenote").innerHTML = data;

  if (document.getElementById("#video_notes_form"))
    document.getElementById("#video_notes_form").scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
};

/**
 * Put player in pause when displaying the form to create a note
 */
document.addEventListener("submit",  (e) => {
  if (!e.target.matches("form.add_video_notes_form")) return;
  e.preventDefault();

  document.getElementById("podvideoplayer").player.pause();
});

/**
 * Set the current time of the player to the timestamp of the note
 */
document.addEventListener("click",   (e) =>{
  if (!e.target.matches("span.timestamp")) return;


  let timestamp = e.target.parentNode.querySelector("span.timestamp").getAttribute("start");
  if (!isNaN(Number(timestamp)))
    document.getElementById("podvideoplayer").player.currentTime(timestamp);
});

/**
 * Handle click on note or comment text for partial or full display
 */
document.addEventListener("click", (e) => {
  if (!e.target.matches("p.note.form") && !e.target.matches("span.comment.form"))
    return;

  let data_form = new FormData(e.target.parentNode);
  send_form_data(
    e.target.getParent.getAttribute("action"),
    data_form,
    "display_notes_place",
    "post"
  );
});

/**
 * Manage hiding create note or comment form on click on document
 */
document.addEventListener("click", function (e) {
  let video_notes = document.getElementById("video_notes_form");
  if (
    video_notes &&
    !video_notes.contains(e.target) &&
    !document.getElementById("podvideoplayer").contains(e.target) &&
    !("timestamp" in e.target.classList)
  ) {
    if (
      video_notes.parentNode.querySelectorAll(".view_video_notes_form.hidden")
        .length
    ) {

      let data_form = new FormData(document.getElementById("video_notes_form")
        .parentNode
        .querySelector(".view_video_notes_form.hidden")
      );
      send_form_data(
        video_notes
          .parentNode
          .querySelector(".view_video_notes_form.hidden")
          .setAttribute("action"),
        data_form,
        "display_notes_place",
        "post"
      );
    } else if (
      video_notes.parentNode.querySelectorAll(".view_video_note_coms_form.hidden")
        .length
    ) {
      let data_form = new FormData(video_notes
        .parentNode
        .querySelector(".view_video_note_coms_form.hidden")
        )
      send_form_data(
        video_notes
          .parentNode
          .querySelector(".view_video_note_coms_form.hidden")
          .getAttribute("action"),
        data_form,
        "display_notes_place",
        "post"
      );
    }
  }
});
document.addEventListener("click",   (e)  =>{
  if (!e.target.matches("#cancel_save")) return;
  let video_notes = document.getElementById("video_notes_form");
  let data_form = new FormData(video_notes.parentNode.querySelector(".view_video_notes_form.hidden"))
   
  send_form_data(
    video_notes
      .parentNode
      .querySelector(".view_video_notes_form.hidden")
      .getAttribute("action"),
    data_form,
    "display_notes_place",
    "post"
  );
});
document.addEventListener("click", "#cancel_save_com",  (e) => {
  if (!e.target.matches("#cancel_save_com")) return;
  let video_notes = document.getElementById("video_notes_form");
  let data_form = new FormData(video_notes.parentNode.querySelector(".view_video_note_coms_form.hidden"))
  send_form_data(
    video_notes
      .parentNode
      .querySelector(".view_video_note_coms_form.hidden")
      .getAttribute("action"),
    data_form,
    "display_notes_place",
    "post"
  );
  
});
