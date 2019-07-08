$(document).on('click', 'span.note', function(){
    let csrf = $('#video_notes_form').find('input[name=csrfmiddlewaretoken]')[0].value;
    let timestamp = $(this).parent().find('span.timestamp').attr('start');
    let input_note = $('textarea#id_note');
    let input_timestamp = $('input#id_timestamp');
    let jqxhr = $.ajax({
        method: 'POST',
        url: $('#video_notes_form').attr('action'),
        data: {'csrfmiddlewaretoken': csrf, 'action': 'get', 'timestamp': timestamp},
        dataType: 'json'
    });
    jqxhr.done(function(data) {
        input_note.val(data['note']);
        input_timestamp.val(data['timestamp']);
        $('input[name=action]').val('save_edit');
    });
    jqxhr.fail(function($xhr) {
        input_note.val('');
    });
})

$(document).on('keydown',  'textarea#id_note', function(e){
    if (e.key == 'Enter') {
        e.preventDefault();
        !$('#id_timestamp').val()?$('#id_timestamp').val(Math.floor($('#podvideoplayer').get(0).player.currentTime())):undefined;
        $('#video_notes_form').submit();
    }
})

$(document).on('click', 'button.remove', function(){
    $('#id_timestamp').val($(this).parent().find('span.timestamp').attr('start'));
    $('input[name=action]').val('remove');
    $('#video_notes_form').submit();
})
