var id_form = 'form_enrich';
function show_form(data) {
    $('#'+id_form).hide().html(data).fadeIn();
    $("input#id_start")
        .before("&nbsp;<span class='getfromvideo pull-right' style='margin-bottom:4px'><a id='getfromvideo_start' class='btn btn-primary btn-sm'>" + gettext('Get time from the player') + "</a><span class='timecode'></span></span>");
    $("input#id_end")
        .before("&nbsp;<span class='getfromvideo pull-right' style='margin-bottom:4px'><a id='getfromvideo_end' class='btn btn-primary btn-sm'>" + gettext('Get time from the player') + "</a><span class='timecode'></span></span>");
    enrich_type();
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

$(document).on('click', '#cancel_enrichment', function() {
    $('form.get_form').show();
    show_form('');
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
            if (data.indexOf('list_enrichment') == -1) {
                showalert(gettext('You are no longer authenticated. Please log in again.'), 'alert-danger');
            } else {
                location.reload();
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
        $('.form-help-inline').parents('div.form-group').removeClass('has-error');
        $('.form-help-inline').remove();
        if (verify_fields() && verify_end_start_items() && overlaptest()) {
            $('form#form_enrich').hide();
            var data_form = $('form#form_enrich').serialize();
            var jqxhr = $.ajax({
                method: 'POST',
                url: window.location.href,
                data: data_form,
                dataType: 'html'
            });
            jqxhr.done(function(data) {
                if (data.indexOf('list_enrichment') == -1 && data.indexOf('form') == -1) {
                    showalert(gettext('You are no longer authenticated. Please log in again.'), 'alert-danger');
                } else {
                    data = JSON.parse(data);
                    if (data.errors) {
                        show_form(data.form);
                        $('form#form_enrich').show();
                    } else {
                        location.reload();
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
            if (data.indexOf('list_enrichment') == -1) {
                showalert(gettext('You are no longer authenticated. Please log in again.'), 'alert-danger');
            } else {
                location.reload();
            }
        });
        jqxhr.fail(function($xhr) {
            var data = $xhr.status + ' : ' + $xhr.statusText;
            ajaxfail(data);
        });
    }
};

/*** Function show the item selected by type field ***/
$(document).on('change', '#page-video select#id_type', function() {
    enrich_type();
});

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

function get_form(data) {
    $("#form_enrich").hide().html(data).fadeIn();
    $("input#id_start")
        .before("&nbsp;<span class='getfromvideo pull-right' style='margin-bottom:4px'><a id='getfromvideo_start' class='btn btn-primary btn-sm'>" + gettext('Get time from the player') + "</a><span class='timecode'></span></span>");
    $("input#id_end")
        .before("&nbsp;<span class='getfromvideo pull-right' style='margin-bottom:4px'><a id='getfromvideo_end' class='btn btn-primary btn-sm'>" + gettext('Get time from the player') + "</a><span class='timecode'></span></span>");
    enrich_type();
    manageResize();
};
function enrich_type(){
    $("#id_image").parents('div.form-group').hide();
    $("textarea#id_richtext").parents('div.form-group:first').hide();
    $("#id_weblink").parents('div.form-group').hide();
    $("#id_document").parents('div.form-group').hide();
    $("#id_embed").parents('div.form-group').hide();
    var val = $("select#id_type").val();
    if (val != '') {
        $("#form_enrich").find('[id^="id_' + val + '"]').parents('div.form-group:first').show();
    }
}
$(document).on('change','#page-video input#id_start',function() {
    $(this).parent().find("span.getfromvideo span.timecode").html(" "+parseInt($(this).val()).toHHMMSS());
});
$(document).on('change','#page-video input#id_end',function() {
    $(this).parent().find("span.getfromvideo span.timecode").html(" "+parseInt($(this).val()).toHHMMSS());
});
$(document).on('click','#page-video span.getfromvideo a',function(e) {
    e.preventDefault();
    if(!(typeof player === 'undefined')) {
        if($(this).attr('id') == "getfromvideo_start"){
            $("input#id_start").val(parseInt(player.currentTime()));
            $("input#id_start").trigger('change');
        } else {
            $("input#id_end").val(parseInt(player.currentTime()));
            $("input#id_end").trigger('change');
        }
    }
});
/*** Verify if value of field respect form field ***/
function verify_fields(){
    var error = false;
    if ( document.getElementById("id_title").value == "" || document.getElementById("id_title").value.length < 2 || document.getElementById("id_title").value.length > 100 ) {
        $("input#id_title")
            .before("<span class='form-help-inline'>&nbsp;&nbsp;" + gettext('Please enter a title from 2 to 100 characters.') + "</span>")
            .parents('div.form-group').addClass('has-error');
        error = true;
    }
    if ( document.getElementById("id_start").value == "" || document.getElementById("id_start").value < 0 || document.getElementById("id_start").value >= video_duration ){
        $("input#id_start")
            .before("<span class='form-help-inline'>&nbsp; &nbsp;" + gettext('Please enter a correct start from 0 to ') + (video_duration -1) + "</span>")
            .parents('div.form-group').addClass('has-error');
        error = true;
    }
    if ( document.getElementById("id_end").value == "" || document.getElementById("id_end").value <= 0 || document.getElementById("id_end").value > video_duration ){
        $("input#id_end")
            .before("<span class='form-help-inline'>&nbsp; &nbsp;" + gettext('Please enter a correct end from 1 to ') + video_duration + "</span>")
            .parents('div.form-group').addClass('has-error');
        error = true;
    }
    switch (document.getElementById("id_type").value){
        case "image":
            if($("#id_image_thumbnail_img").attr('src') == "/static/filer/icons/nofile_48x48.png"){ //check with id_image value
                $("img#id_image_thumbnail_img")
                    .before("<span class='form-help-inline'>&nbsp; &nbsp;" + gettext('Please enter a correct image.') + "</span>")
                    .parents('div.form-group').addClass('has-error');
                error = true;
            }
            break;
        case "richtext":
            if(document.getElementById("id_richtext").value == ""){
                $("textarea#id_richtext")
                    .before("<span class='form-help-inline'>&nbsp; &nbsp;" + gettext('Please enter a correct richtext.') + "</span>")
                    .parents('div.form-group').addClass('has-error');
                error = true;
            }
            break;
        case "weblink":
            if(document.getElementById("id_weblink").value == ""){
                $("input#id_weblink")
                    .before("<span class='form-help-inline'>&nbsp; &nbsp;" + gettext('Please enter a correct weblink.') + "</span>")
                    .parents('div.form-group').addClass('has-error');
                error = true;
            } else {
                if(document.getElementById("id_weblink").value > 200){
                    $("input#id_weblink")
                        .before("<span class='form-help-inline'>&nbsp; &nbsp;" + gettext('Weblink must be less than 200 characters.') + "</span>")
                        .parents('div.form-group').addClass('has-error');
                    error = true;
                }
            }
            break;
        case "document":
            if($("#id_document_thumbnail_img").attr('src') == "/static/filer/icons/nofile_48x48.png"){ //check with id_document value
                $("img#id_document_thumbnail_img")
                    .before("<span class='form-help-inline'>&nbsp; &nbsp;" + gettext('Please select a document.') +  "</span>")
                    .parents('div.form-group').addClass('has-error');
                error = true;
            }
            break;
        case "embed":
            if(document.getElementById("id_embed").value == ""){
                $("textarea#id_embed")
                    .before("<span class='form-help-inline'>&nbsp; &nbsp;" + gettext('Please enter a correct embed.') + "</span>")
                    .parents('div.form-group').addClass('has-error');
                error = true;
            } else {
                if(document.getElementById("id_embed").value > 300){
                    $("input#id_weblink")
                    .before("<span class='form-help-inline'>&nbsp; &nbsp;" + gettext('Embed field must be less than 300 characters.') + "</span>")
                    .parents('div.form-group').addClass('has-error');
                error = true;
                }
            }
            break;
        default:
            $("select#id_type")
                .before("<span class='form-help-inline'>&nbsp; &nbsp;" + gettext('Please enter a type in index field.') + "</span>")
                .parents('div.form-group').addClass('has-error');
            error = true;
    }
    return !error;
};
/***  Verify if fields end and start are correct ***/
function verify_end_start_items(){
    var msg = "";
    new_start = parseInt(document.getElementById("id_start").value);
    new_end = parseInt(document.getElementById("id_end").value);
    if(new_start > new_end){
        msg = gettext('The start field value is greater than the end field one.');
    }else if(new_end > video_duration){
        msg = gettext('The end field value is greater than the video duration.');
    }else if (new_start == new_end){
        msg = gettext('End field and start field cannot be equal.');
    }
    if (msg) {
        return msg;
    }
    return true;
};
/*** Verify if there is a overlap with over enrich***/
function overlaptest(){
    //var video_list_enrich=[];
    var new_start = parseInt(document.getElementById("id_start").value);
    var new_end = parseInt(document.getElementById("id_end").value);
    var id = document.getElementById("id_enrich").value;
    var msg = "";
    $('ul#slides li').each(function() {
        var data_start = parseInt($(this).attr('data-start'));
        var data_end = parseInt($(this).attr('data-end'));
        if (id != $(this).attr('data-id') && !(new_start< data_start && new_end <= data_start || new_start >= data_end &&  new_end > data_end)){
            var text = gettext('There is an overlap with the enrichment ') + '"' + $(this).attr('data-title') + '"' ;
            text += ", " + gettext('please change start and/or end values.');
            msg+="<br/>"+ text ;
        }
    });
    if (msg) {
        return msg;
    }
    return true;
};