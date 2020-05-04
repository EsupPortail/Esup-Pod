var id_form = "form_chapter";
function show_form(data) {
    $('#'+id_form).hide().html(data).fadeIn();
    $("input#id_time_start")
        .before("&nbsp;<span class='getfromvideo pull-right' style='margin:0;margin-bottom:4px'><a id='getfromvideo_start' class='btn btn-primary btn-sm text-white'>" + gettext('Get time from the player') + "</a><span class='timecode' style='font-size: 12px;'>&nbsp;</span></span>");
    $("input#id_time_end")
        .before("&nbsp;<span class='getfromvideo pull-right' style='margin:0;margin-bottom:4px'><a id='getfromvideo_end' class='btn btn-primary btn-sm text-white'>" + gettext('Get time from the player') + "</a><span class='timecode' style='font-size: 12px;'>&nbsp;</span></span>");
};

var showalert = function(message, alerttype) {
    $('body').append('<div id="formalertdiv" class="alert ' + alerttype + ' alert-dismissible fade show" role="alert">' + message + '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button></div>');
    setTimeout(function() { $("#formalertdiv").remove(); }, 5000);
};

var ajaxfail = function(data) {
    showalert(gettext('Error getting form.') + ' (' + data + ') ' + gettext('The form could not be recovered.'), 'alert-danger');
    $('form.get_form').show();
    show_form('');
};

$(document).on('click', '#cancel_chapter', function() {
    $('form.get_form').show();
    show_form('');
    $('#fileModal_id_file').remove();
});

$(document).on('submit', 'form.get_form', function(e) {
    e.preventDefault();
    var jqxhr = '';
    var action = $(this).find('input[name=action]').val();
    sendandgetform(this, action);
});

$(document).on('submit', 'form.form_save', function(e) {
    e.preventDefault();
    var jqxhr = '';
    var action = $(this).find('input[name=action]').val();
    sendform(this, action);
});

var sendandgetform = function(elt, action) {
    $('form.get_form').hide();
    if (action == 'new') {
        var jqxhr = $.ajax({
            method: 'POST',
            url: window.location.href,
            data: {'action': 'new', 'csrfmiddlewaretoken': $(elt).find('input[name="csrfmiddlewaretoken"]').val()},
            dataType: 'html'
        });
        jqxhr.done(function(data) {
            if (data.indexOf(id_form) == -1) {
                showalert(gettext('You are no longer authenticated. Please log in again.'), 'alert-danger');
            } else {
                show_form(data);
            }
        });
        jqxhr.fail(function($xhr) {
            var data = $xhr.status + ' : ' + $xhr.statusText;
            ajaxfail(data);
        });
    }
    if (action == 'modify') {
        var id = $(elt).find('input[name=id]').val();
        var jqxhr = $.ajax({
            method: 'POST',
            url: window.location.href,
            data: {'action': 'modify', 'id': id, 'csrfmiddlewaretoken': $(elt).find('input[name="csrfmiddlewaretoken"]').val()},
            dataType: 'html'
        });
        jqxhr.done(function(data) {
            if (data.indexOf(id_form) == -1) {
                showalert(gettext('You are no longer authenticated. Please log in again.'), 'alert-danger');
            } else {
                show_form(data);
                $(elt).addClass('info');
            }
        });
        jqxhr.fail(function($xhr) {
            var data = $xhr.status + ' : ' + $xhr.statusText;
            ajaxfail(data);
        });
    }
    if (action == 'delete') {
        var id = $(elt).find('input[name=id]').val();
        var jqxhr = $.ajax({
            method: 'POST',
            url: window.location.href,
            data: {'action': 'delete', 'id': id, 'csrfmiddlewaretoken': $(elt).find('input[name="csrfmiddlewaretoken"]').val()},
            dataType: 'html'
        });
        jqxhr.done(function(data) {
            if (data.indexOf('list_chapter') == -1) {
                showalert(gettext('You are no longer authenticated. Please log in again.'), 'alert-danger');
            } else {
                data = JSON.parse(data);
                //location.reload();
                updateDom(data);
                manageDelete();
                $(list_chapter).html(data['list_chapter']);
                show_form('');
                $('form.get_form').show();
            }
        });
        jqxhr.fail(function($xhr) {
            var data = $xhr.status + ' : ' + $xhr.statusText;
            ajaxfail(data);
        });
    }
};

var sendform = function(elt, action) {
    if (action == 'save') {
        if (verify_start_title_items()) {
            $('form#form_chapter').hide();
            var data_form = $('form#form_chapter').serialize();
            var jqxhr = $.ajax({
                method: 'POST',
                url: window.location.href,
                data: data_form,
                dataType: 'html'

            });
            jqxhr.done(function(data) {
                if (data.indexOf('list_chapter') == -1 && data.indexOf('form') == -1) {
                    showalert(gettext('You are no longer authenticated. Please log in again.'), 'alert-danger');
                } else {
                    data = JSON.parse(data);
                    if (data.errors) {
                        show_form(data.form);
                        $('form#form_chapter').show();
                    } else {
                        //location.reload();
                        updateDom(data);
                        manageSave();
                        $(list_chapter).html(data['list_chapter']);
                        show_form('');
                        $('form.get_form').show();
                    }
                }
            });
            jqxhr.fail(function($xhr) {
                var data = $xhr.status + ' : ' + $xhr.statusText;
                ajaxfail(data);
            });
        } else {
            showalert(gettext('One or more errors have been found in the form.'), 'alert-danger');
        }
    }
    if (action == 'import') {
        var file = $(elt).find('input[name=file]').val();
        var jqxhr = $.ajax({
            method: 'POST',
            url: window.location.href,
            data: {'action': 'import', 'file': file, 'csrfmiddlewaretoken': $(elt).find('input[name="csrfmiddlewaretoken"]').val()},
            dataType: 'html'
        });
        jqxhr.done(function(data) {
            if (data.indexOf('list_chapter') == -1) {
                showalert(gettext('You are no longer authenticated. Please log in again.'), 'alert-danger');
            } else {
                //location.reload();
                data = JSON.parse(data);
                updateDom(data);
                manageImport();
                $(list_chapter).html(data['list_chapter']);
                show_form('');
                $('form.get_form').show();
            }
        });
        jqxhr.fail(function($xhr) {
            var data = $xhr.status + ' : ' + $xhr.statusText;
            ajaxfail(data);
        });
    }
};

/*** Verify if value of field respect form field ***/
function verify_start_title_items(){
    if ( document.getElementById("id_title").value == "" || document.getElementById("id_title").value.length < 2 || document.getElementById("id_title").value.length > 100 ) {
        $("input#id_title")
            .before("<span class='form-help-inline'>&nbsp;&nbsp;" + gettext('Please enter a title from 2 to 100 characters.') + "</span>")
            .parents('div.form-group').addClass('has-error');
        return false;
    }
    if ( document.getElementById("id_time_start").value == "" || document.getElementById("id_time_start").value < 0 || document.getElementById("id_time_start").value >= video_duration) {
        $("input#id_time_start")
            .before("<span class='form-help-inline'>&nbsp;&nbsp;" + gettext('Please enter a correct start field between 0 and') + " " + (video_duration -1) + "</span>")
            .parents('div.form-group').addClass('has-error');
        return false;
    }
    return true;
};

function overlaptest(){
    var new_start = parseInt(document.getElementById("id_time_start").value);
  	var id = parseInt(document.getElementById("id_chapter").value);
    var msg = "";
    $('ul#chapters li').each(function() {
        if ((id != $(this).attr('data-id')) && new_start == $(this).attr('data-start')) {
            var text = gettext('The chapter') + ' "' + $(this).attr('data-title') + '" ' + gettext('starts at the same time.');
            msg+="<br/>"+ text ;
        }
    });
    return msg;
};

/*** Display element of form enrich ***/
Number.prototype.toHHMMSS = function() {
    var seconds = Math.floor(this),
        hours = Math.floor(seconds / 3600);
    seconds -= hours*3600;
    var minutes = Math.floor(seconds / 60);
    seconds -= minutes*60;

    if (hours   < 10) {hours   = "0"+hours;}
    if (minutes < 10) {minutes = "0"+minutes;}
    if (seconds < 10) {seconds = "0"+seconds;}
    return hours+':'+minutes+':'+seconds;
};

$(document).on('change','input#id_time_start',function() {
    $(this).parent().find("span.getfromvideo span.timecode").html(" "+parseInt($(this).val()).toHHMMSS());
});
$(document).on('change','input#id_time_end',function() {
    $(this).parent().find("span.getfromvideo span.timecode").html(" "+parseInt($(this).val()).toHHMMSS());
});

$(document).on('click','#info_video span.getfromvideo a',function(e) {
    e.preventDefault();
    if(!(typeof player === 'undefined')) {
        if($(this).attr('id') == "getfromvideo_start"){
            $("input#id_time_start").val(parseInt(player.currentTime()));
            $("input#id_time_start").trigger('change');
        }
    }
});



var updateDom = function(data) {
    let player = window.videojs.players.podvideoplayer;
    let n1 = document.querySelector('ul#chapters');
    let n2 = document.querySelector('div.chapters-list');
    let tmp_node = document.createElement('div');
    $(tmp_node).html(data['video-elem']);
    let chaplist  = tmp_node.querySelector('div.chapters-list');
    if (n1 != null) {
        n1.parentNode.removeChild(n1);
    }
    if (n2 != null) {
        n2.parentNode.removeChild(n2);
    }
    if (chaplist != null && n2 != null) {
        chaplist.className = n2.className;
    }
    $("#" + window.videojs.players.podvideoplayer.id_).append(chaplist);
    $("#" + window.videojs.players.podvideoplayer.id_).append(tmp_node.querySelector('ul#chapters'));
}

var manageSave = function() {
    let player = window.videojs.players.podvideoplayer;
    if(player.usingPlugin('videoJsChapters')) {
        player.main();
    }
    else {
        player.videoJsChapters();
    }
}

var manageDelete = function() {
    let player = window.videojs.players.podvideoplayer;
    let n = document.querySelector('div.chapters-list');
    if(n != null) {
        player.main();
    }
    else {
        player.controlBar.chapters.dispose();
        player.videoJsChapters().dispose();
    }
}

var manageImport = function() {
    let player = window.videojs.players.podvideoplayer;
    let n = document.querySelector('div.chapters-list');
    if(n != null) {
        if(player.usingPlugin('videoJsChapters')) {
            player.main();
        }
        else {
            player.videoJsChapters();
        }
    }
    else {
        if(typeof(player.controlBar.chapters) != 'undefined') {
            player.controlBar.chapters.dispose();
        }
        if(player.usingPlugin('videoJsChapters')) {
            player.videoJsChapters().dispose();
        }
    }
}