/**
 * Handle enter key pressed while editing note or comment
 */
$(document).on('keydown',  'textarea#id_note, textarea#id_comment', function(e){
    if (e.key == 'Enter') {
        e.preventDefault();
        if (this.id == "id_note")
            !$('#id_timestamp').val()?$('#id_timestamp').val(Math.floor($('#podvideoplayer').get(0).player.currentTime())):undefined;
        $('#video_notes_form').submit();
    }
})

$(document).on('click',  '#video_notes_form_save', function(e){
    !$('#id_timestamp').val()?$('#id_timestamp').val(Math.floor($('#podvideoplayer').get(0).player.currentTime())):undefined;
    $('#video_notes_form').submit();
})

/**
 * Handle click on buttons in three dots menu
 */
$(document).on('submit', '#video_notes_form, div.mgtNotes form, div.mgtNote form, div.mgtComment form', function(e) {
    if ($(this).attr('class') != 'download_video_notes_form') {
        e.preventDefault();
        let data_form = $(this).serializeArray();
        send_form_data($(this).attr("action"), data_form, "display_notes_place", "post");
    }
})

/**
 * Fill allocated space for notes and comments with content
 */
var display_notes_place = function(data) {
    $( "div#card-takenote" ).html(data);
    feather.replace({ class: 'align-bottom'});
    if($('#video_notes_form').length)
        $('#video_notes_form')[0].scrollIntoView({
            behavior: "smooth",
            block: "end"
        });
}

/**
 * Put player in pause when displaying the form to create a note
 */
$(document).on('submit', 'form.add_video_notes_form', function() {
    $('#podvideoplayer').get(0).player.pause();
})

/**
 * Set the current time of the player to the timestamp of the note
 */
$(document).on('click', 'span.timestamp', function(){
    let timestamp = $(this).parent().find('span.timestamp').attr('start');
    if (!isNaN(Number(timestamp)))
        $('#podvideoplayer').get(0).player.currentTime(timestamp);
})

/**
 * Handle click on note or comment text for partial or full display
 */
$(document).on('click', 'p.note.form, span.comment.form', function(){
    let data_form = $(this).parent().serializeArray();
    send_form_data($(this).parent().attr("action"), data_form, "display_notes_place", "post");
})

/**
 * Manage hiding create note or comment form on click on document
 */
$(document).on('click', function(e) {
    if ($("#video_notes_form").length
            && !$("#video_notes_form")[0].contains(e.target)
            && !$('#podvideoplayer').get(0).contains(e.target)
            && !("timestamp" in e.target.classList)) {
        if ($("#video_notes_form").parent().find('.view_video_notes_form.hidden').length) {
            let data_form = $("#video_notes_form").parent().find('.view_video_notes_form.hidden').serializeArray();
            send_form_data($("#video_notes_form").parent().find('.view_video_notes_form.hidden').attr("action"), data_form, "display_notes_place", "post");
        }
        else if ($("#video_notes_form").parent().find('.view_video_note_coms_form.hidden').length) {
            let data_form = $("#video_notes_form").parent().find('.view_video_note_coms_form.hidden').serializeArray();
            send_form_data($("#video_notes_form").parent().find('.view_video_note_coms_form.hidden').attr("action"), data_form, "display_notes_place", "post");
        }
    }
})
$(document).on('click', '#cancel_save', function(){
    let data_form = $("#video_notes_form").parent().find('.view_video_notes_form.hidden').serializeArray();
    send_form_data($("#video_notes_form").parent().find('.view_video_notes_form.hidden').attr("action"), data_form, "display_notes_place", "post");
})
$(document).on('click', '#cancel_save_com', function(){
    let data_form = $("#video_notes_form").parent().find('.view_video_note_coms_form.hidden').serializeArray();
    send_form_data($("#video_notes_form").parent().find('.view_video_note_coms_form.hidden').attr("action"), data_form, "display_notes_place", "post");
})
