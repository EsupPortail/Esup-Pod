/**
 * Handle enter key pressed while editing note or comment
 */
$(document).on('keydown',  'textarea#id_note', function(e){
    if (e.key == 'Enter') {
        e.preventDefault();
        !$('#id_timestamp').val()?$('#id_timestamp').val(Math.floor($('#podvideoplayer').get(0).player.currentTime())):undefined;
        $('#video_notes_form').submit();
    }
})

$(document).on('keydown',  'textarea#id_comment', function(e){
    if (e.key == 'Enter') {
        e.preventDefault();
        $('#video_notes_form').submit();
    }
})


$(document).on('submit', '#video_notes_form, div.mgtNote form', function(e) {
    if ($(this).attr('class') != 'download_video_notes_form') {
        e.preventDefault();
        let data_form = $(this).serializeArray();
        send_form_data($(this).attr("action"), data_form, "show_form_notes", "post");
    }
})


/**
 * Form displaying for note or comment
 */
var show_form_notes = function(data) {
    $( "div#id_notes" ).parent().html(data);
    feather.replace({ class: 'align-bottom'});
    if($('#video_notes_form').length)
        $('#video_notes_form')[0].scrollIntoView({
            behavior: "smooth",
            block: "end"
        });
}

/**
 * Display the form to add a note on click on add button
 */
$(document).on('click', 'button#addNote', function() {
    $('#podvideoplayer').get(0).player.pause();
})

/**
 * Set the current time of the player to the timestamp of the note
 */
$(document).on('click', 'span.timestamp', function(){
    let timestamp = $(this).parent().find('span.timestamp').attr('start');
    $('#podvideoplayer').get(0).player.currentTime(timestamp);
})

$(document).on('click', 'p.note.form, p.comment.form', function(){
    let data_form = $(this).parent().serializeArray();
    send_form_data($(this).parent().attr("action"), data_form, "show_form_notes", "post");
})

$(document).on('click', function(e) {
    if ($("#video_notes_form").length && !$("#video_notes_form")[0].contains(e.target)) {
        let data_form = $("#video_notes_form").parent().find('.view_video_notes_form.hidden').serializeArray();
        send_form_data($(this).find('.view_video_notes_form').attr("action"), data_form, "show_form_notes", "post");
    }
})