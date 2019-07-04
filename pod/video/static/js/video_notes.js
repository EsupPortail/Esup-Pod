if (typeof(window['video_notes']) == 'undefined') {
    window['video_notes'] = true;

    $(document).on('click', 'span.note', function(){
        let csrf = $('#video_notes_form').find('input[name=csrfmiddlewaretoken]')[0].value;
        let id = $(this).parent().attr('id').split('-')[1];
        let elt = this;
        let input = $('textarea.input_note');
        let jqxhr = $.ajax({
            method: 'POST',
            url: $('#video_notes_form').attr('action'),
            data: {'csrfmiddlewaretoken': csrf, 'action': 'get', 'note_id': id},
            dataType: 'json'
        });
        jqxhr.done(function(data) {
            input.attr('action', 'save_edit');
            input.attr('id', 'note-' + id);
            input.val(data['note']);
        });
        jqxhr.fail(function($xhr) {
            input.val('');
        });
    })

    $(document).on('click', 'span.timestamp', function(){
        $('#podvideoplayer').get(0).player.currentTime($(this).attr('start'));
    })

    // $(document).on('blur', 'textarea.input_note', function(){
    //     updateDistantNote(this);
    // })
    $(document).on('keydown',  'textarea.input_note', function(e){
        if (e.key == 'Enter') {
            updateDistantNote(this);
            e.preventDefault();
        }
    })

    $(document).on('click', 'button.remove', function(){
        updateDistantNote(this);
    })
}

updateDistantNote = function(elt){
    let csrf = $('#video_notes_form').find('input[name=csrfmiddlewaretoken]')[0].value;
    let action = $(elt).attr('action');
    let data = {'csrfmiddlewaretoken': csrf, 'action': action};
    if (action == 'save_new'){
        let timestamp = $('#podvideoplayer').get(0).player.currentTime();
        var note = $('textarea.input_note').val();
        data["timestamp"] = Math.floor(timestamp);
        data["note"] = note;
    }
    else if (action == 'save_edit'){
        var id = $(elt).attr('id').split('-')[1];
        let timestamp = $('div#note-' + id).find('span.timestamp').attr('start');
        var note = $('textarea.input_note').val();
        data["note_id"] = id;
        data["timestamp"] = timestamp;
        data["note"] = note;
    }
    else if (action == 'remove'){
        var id = $(elt).parent().attr('id').split('-')[1];
        data["note_id"] = id;
    }
    let jqxhr = $.ajax({
        method: 'POST',
        url: $('#video_notes_form').attr('action'),
        data: data,
        dataType: 'html'
    });
    jqxhr.done(function(data) {
        $('#video_notes_form').parent().html(JSON.parse(data)['render']);
        if (JSON.parse(data)['status'] =='error') {
            $('input_note').val(note);
            $('input_note').attr('action', action);
            (typeof(id)!="undefined")?input.attr('id', 'note-' + id):undefined;
        }
        (action == 'save_new' || action == 'save_edit')?$('.input_note').focus():undefined;
    })
}