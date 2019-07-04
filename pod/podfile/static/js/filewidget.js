/** SELECT FILE **/
$(document).on("click", "a.file-name", function(e) {
    e.preventDefault();
    $("#"+id_input).val($(this).data("id"));
    $(".btn-fileinput").html(gettext('Change file'));
    $("#fileinput_"+id_input).html($(this).html());
    $("#modal-folder_"+id_input).html("");
    $('#fileModal_'+id_input).modal('hide');
});


/** FOLDER **/
$(document).on('click', '#list_folder .edit', function(){
    $('#id_name').val($(this).data('name'));
    $('#id_folder').val($(this).data('id'));
    $('#list_folder .edit').hide();
    $('#list_folder .delete').hide();
    $(this).parents('div.list-group-item').addClass('list-group-item-info');
});

$(document).on('click', '#form_folder_cancel', function(e){
    e.preventDefault();
    $('#id_name').val("");
    $('#id_folder').val("");
    $('#list_folder .edit').show();
    $('#list_folder .delete').show();
    $('div.list-group-item').removeClass('list-group-item-info');
});

$(document).on('submit', '#list_folder form.delete_folder', function(e){
    e.preventDefault();
    var deleteConfirm = confirm(gettext("Are you sure you want to delete this folder?"));
    if (deleteConfirm){
        send_form_data($(this).attr("action"), $(this).serializeArray(), "append_folder_html_in_modal");
    }
});

$(document).on('click', 'a.form_folder_files', function(e){
    e.preventDefault();
    send_form_data($(this).attr('href'), {}, "append_files_html_in_modal", "get");
});

$(document).on('submit', '#form_folder', function(e){
    e.preventDefault();
    var data_form = $(this).serializeArray();
    send_form_data($(this).attr("action"), data_form, "append_folder_html_in_modal");
});

var append_folder_html_in_modal = function(data) {
    $("#modal-folder_"+id_input).html(data);
    feather.replace({ class: 'align-bottom'});
}

var append_files_html_in_modal = function(data) {
    $("#list_file").html(data);
    $('div.list-group-item').removeClass('list-group-item-success');
    $('#'+$("#current_folder_name").data('id')).addClass('list-group-item-success');
    feather.replace({ class: 'align-bottom'});
}


/** FILE **/
if(typeof(window['form.get_form_fileSubmitEvt']) == 'undefined') {
    window['form.get_form_fileSubmitEvt'] = true;
    $(document).on("submit", "form.get_form_file", function (e) {
        e.preventDefault();
        $("form.get_form_file").hide();
        $("#formeditfile").remove();
        var action = $(this).find('input[name=action]').val(); // new, modify and delete
        if(action == "delete") {
            var deleteConfirm = confirm(gettext("Are you sure you want to delete this element?"));
            if (deleteConfirm) {
                send_form_data($(this).attr('action'), $(this).serializeArray(), "show_form_file_" + action);
            }
            else {
                $("form.get_form_file").show();
            }
        }
        else {
            send_form_data($(this).attr('action'), $(this).serializeArray(), "show_form_file_" + action);
        }
    });
}

if(typeof(window['form#formeditfileSubmitEvt']) == 'undefined') {
    window['form#formeditfileSubmitEvt'] = true;
    $(document).on("submit", "form#formeditfile", function (e) {
        e.preventDefault();
        var data_form = new FormData($('#formeditfile')[0]);
        if ($(this).find('input[name=captionMaker]').length) {
            data_form.delete('file');
            rxSignatureLine = /^WEBVTT(?:\s.*)?$/;
            vttContent = CreateVTTSource();
            vttLines = vttContent.split(/\r\n|\r|\n/);
            if (!rxSignatureLine.test(vttLines[0])) {
                alert("Not a valid time track file.");
                return;
            }
            if (typeof($('#id_filename')[0]) == 'undefined') {
                id = $('#formeditfile').children('#id_file')[0].value;
                name = $('a.file-name[data-id='+id+']').children('strong')[0].innerHTML;
            }
            else {
                name = $('#id_filename')[0].value;
            }
            if (typeof(name) != 'undefined' && name != "") {
                f = new File([vttContent], name + '.vtt', {type: 'text/vtt'});
                data_form.append('file', f);
            }
        }
        $.ajax({
            url: $( "#formeditfile" ).attr("action"), 
            type: 'POST',
            data: data_form,
            processData: false,
            contentType: false                    
        }).done(function(data){
            show_save_file_form(data);
        }).fail(function($xhr){
            var data = $xhr.status+ " : " +$xhr.statusText;
            showalert(gettext("Error during exchange") + "("+data+")<br/>"+gettext("No data could be stored."), "alert-danger");
        });
    });
}

if(typeof(window['form#formeditfileResetEvt']) == 'undefined') {
    window['form#formeditfileResetEvt'] = true;
    $(document).on("reset", "form#formeditfile", function (e) {
        e.preventDefault();
        $('#list_file .list-group-item-action').show();
        $("form.get_form_file").show();
        $("#editfile").remove();
    });
}

$(document).on("change", "#id_file", function (e) {
    var fileSize = $(this).get(0).files[0].size;
    var maxsize = parseInt($(this).data('maxsize'));
    if(fileSize>maxsize){
        showalert(gettext("The file size exceeds the maximum allowed value :")+" "+VIDEO_MAX_UPLOAD_SIZE+" Go.","alert-danger");
    }
});

var show_form_file_new = function(data) {
    $('#list_file .list-group-item-action').hide();
    $('#list_file').append(data);
}

var show_form_file_modify = function(data) {
    $('#list_file .list-group-item-action').hide();
    $('#list_file').append(data);
}

var show_form_file_delete = function(data) {
    if(data.list_element) {
        $('#list_file').html(data.list_element);
        feather.replace({ class: 'align-bottom'});
    } else {
        showalert(gettext('You are no longer authenticated. Please log in again.'), "alert-danger");
    }
}

var show_save_file_form = function(data) {
    if(data.list_element || data.form) {
        if(data.errors){
            showalert(gettext('One or more errors have been found in the form.'), "alert-danger");
            $("#editfile").remove();
            show_form_file_new(data.form);
        }else{
            $('#list_file').html(data.list_element);
            feather.replace({ class: 'align-bottom'});
        }
    } else {
        showalert(gettext('You are no longer authenticated. Please log in again.'), "alert-danger");
    }
}

var send_form_data = function(url,data_form, fct, method="post") {
    var jqxhr= '';
    if(method=="post") jqxhr = $.post(url, data_form);
    else jqxhr = $.get(url);
    jqxhr.done(function(data){ window[fct](data); });
    jqxhr.fail(function($xhr) {
        var data = $xhr.status+ " : " +$xhr.statusText;
        showalert(gettext("Error during exchange") + "("+data+")<br/>"+gettext("No data could be stored."), "alert-danger");
    });
}