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
        $('#video_notes_comments_form').submit();
    }
})


/**
 * Handle click on update button
 */
$(document).on("submit", "#update_video_notes_form", function(e) {
    e.preventDefault();
    var data_form = $(this).serializeArray();
    send_form_data($(this).attr("action"), data_form, "show_form_notes", "post");
});

$(document).on("submit", "#update_video_notes_com_form", function(e) {
    e.preventDefault();
    var data_form = $(this).serializeArray();
    send_form_data($(this).attr("action"), data_form, "show_form_notes_com", "post");
});


/**
 * Handle click on edit button
 */
$(document).on('submit', 'form.edit_video_notes_form', function(e) {
    e.preventDefault();
    let timestamp = $(this).parent().find('span.timestamp').attr('start');
    let data_form = $(this).serializeArray();
    data_form.push({name: 'timestamp', value: timestamp});
    send_form_data($(this).attr("action"), data_form, "display_note_edit", "post");
})

$(document).on('submit', 'form.edit_video_notes_com_form', function(e) {
    e.preventDefault();
    let data_form = $(this).serializeArray();
    send_form_data($(this).attr("action"), data_form, "display_note_com_edit", "post");
})


/**
 * Handle click on remove button
 */
$(document).on('submit', 'form.remove_video_notes_form', function(e){
    e.preventDefault();
    let timestamp = $(this).parent().find('span.timestamp').attr('start');
    let data_form = $(this).serializeArray();
    data_form.push({name: 'timestamp', value: timestamp});
    send_form_data($(this).attr("action"), data_form, "show_form_notes", "post");
})

$(document).on('submit', 'form.remove_video_notes_com_form', function(e){
    e.preventDefault();
    let data_form = $(this).serializeArray();
    send_form_data($(this).attr("action"), data_form, "show_form_notes_com", "post");
})


/**
 * Handle click on note comment button
 */
$(document).on('submit', 'form.comment_video_notes_form', function(e){
    e.preventDefault();
    let data_form = $(this).serializeArray();
    send_form_data($(this).attr("action"), data_form, "show_form_notes", "post");
})


/**
 * Handle click on note view button
 */
$(document).on('submit', 'form.view_video_notes_form', function(e){
    e.preventDefault();
    let timestamp = $(this).parent().find('span.timestamp').attr('start');
    let data_form = $(this).serializeArray();
    data_form.push({name: 'timestamp', value: timestamp});
    send_form_data($(this).attr("action"), data_form, "display_note_view", "post");
})

// $(document).on('click', 'p.comment', function(){
//     let data_form = $(this).parent().serializeArray();
//     send_form_data($(this).parent().attr("action"), data_form, "display_note_com_view", "post");
// })


/**
 * Displaying for note or comment editing
 */
var display_note_edit = function(data) {
    $('textarea#id_note').val(data['note']);
    $('input#id_save').val(data['idnote']);
    $('input#id_timestamp').val(data['timestamp']);
    $('select#id_status').val(data['statusnote']);
    $('#video_notes_form').find('input[name=action]').val('save_edit');
}

var display_note_com_edit = function(data) {
    $('textarea#id_comment').val(data['comment']);
    $('input#id_save').val(data['idcom']);
    $('select#id_status').val(data['statuscom']);
    $('#video_notes_comments_form').find('input[name=action]').val('save_edit');
}


/**
 * Displaying note or comment for reading
 */
var display_note_view = function(data) {
    $( "div#id_notes" ).parent().html(data);
    $( "div#id_notes" ).addClass("display_note");
    feather.replace({ class: 'align-bottom'});
}

var display_note_com_view = function(data) {
    $('#video_notes_comments_form').remove();
    $( "div#id_comments" ).html(data['comment']);
    $( "div#id_comments" ).addClass("display_comment");
}


/**
 * Form displaying for note or comment
 */
var show_form_notes = function(data) {
    if ($("div#id_comments").length)
        $( "div#id_comments" ).parent().html(data);
    else if ($("div#id_notes").length)
        $( "div#id_notes" ).parent().html(data);
    feather.replace({ class: 'align-bottom'});
}

var show_form_notes_com = function(data) {
    $( "div#id_comments" ).parent().html(data);
    feather.replace({ class: 'align-bottom'});
}


/**
 * Form submit
 */
$(document).on("submit", "#video_notes_form", function (e) {
    e.preventDefault();
    var data_form = $(this).serializeArray();
    send_form_data($(this).attr("action"), data_form, "show_form_notes", "post");
});

$(document).on("submit", "#video_notes_comments_form", function (e) {
    e.preventDefault();
    var data_form = $(this).serializeArray();
    send_form_data($(this).attr("action"), data_form, "show_form_notes_com", "post");
});



/**
 * Display the form to add a note on click on add button
 */
$(document).on('click', 'button#addNote', function() {
    $('#podvideoplayer').get(0).player.pause();
    let timestamp = $('#podvideoplayer').get(0).player.currentTime();
    $('input#id_timestamp').val(timestamp);
    $('#video_notes_form').show();
})

/**
 * Set the current time of the player to the timestamp of the note
 */
$(document).on('click', 'span.timestamp', function(){
    let timestamp = $(this).parent().find('span.timestamp').attr('start');
    $('#podvideoplayer').get(0).player.currentTime(timestamp);
})


$(document).on('click', 'p.note', function(){
    let data_form = $(this).parent().serializeArray();
    send_form_data($(this).parent().attr("action"), data_form, "display_note_view", "post");
})





// var el = document.querySelector('.more');
// var btn = el.querySelector('.more-btn');
// var menu = el.querySelector('.more-menu');
var visible = false;

function hideMenu(e) {
    if (btn.contains(e.target)) {
        return;
    }
    if (visible) {
        visible = false;
        el.classList.remove('show-more-menu');
        menu.setAttribute('aria-hidden', true);
        document.removeEventListener('mousedown', hideMenu);
    }
}

$(document).on('click', "button.more-btn", function(e) {
    if (!visible) {
        let btn = this; // 3 dots button
        let el = $(btn).parent();
        let menu = el.find('.more-menu');
        visible = true;
        el.addClass('show-more-menu');
        menu.attr('aria-hidden', false);
        let hideMenu = function(e) {
            if (visible && !btn.contains(e.target)) {
                visible = false;
                el.removeClass('show-more-menu');
                menu.attr('aria-hidden', true);
                $(document).off('click', hideMenu);
            }
        };
        $(document).on('click', hideMenu);
    }
});


$(document).on('click', 'div.notdisplayed p.comment', function() {
    $(this).parent().removeClass('notdisplayed');
    $(this).parent().addClass('displayed');
})
$(document).on('click', 'div.displayed p.comment', function() {
    $(this).parent().removeClass('displayed');
    $(this).parent().addClass('notdisplayed');
})
