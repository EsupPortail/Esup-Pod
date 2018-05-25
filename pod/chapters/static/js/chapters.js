$(window).on('load', function() {
	manageResize();
});

function manageResize() {
	var $table = $('table.scroll'),
	    $bodyCells = $table.find('tbody tr:first').children(),
	    colWidth;
	    // Adjust the width of thead cells when window resizes
	    $(window).resize(function() {
	    	// Get the tbody columns width array
	    	colWidth = $bodyCells.map(function() {
	    		return $(this).width();
	    	}).get();
	    	// Set the width of thead columns
	    	$table.find('thead tr').children().each(function(i, v) {
	    		$(v).width(colWidth[i]);
	    	});
	    }).resize(); // Trigger resize handler
}

/*** Every button processing expects cancel
    On modify or new action, all buttons in the first page of enrichment
        are hidden and the form is displayed.
    On delete action, a request is sent with the enrich id.
    On save action, a request is sent with the form after a pair of
        validation functions are runned.
***/
$(document).on("submit", "#formcontent", function (e) {
    $(this).show();
    e.preventDefault();
    var jqxhr= '';
    var action = $(this).find('input[name=action]').val();
    if (action == "save") {
        $('form#form_new').hide();
        $('form.form_modif').hide();
        $('form.form_delete').hide();
        $(".form-help-inline").parents('div.form-group').removeClass("has-error");
        $(".form-help-inline").remove();
        verify_start_title_items();
        if (!($("span").hasClass("form-help-inline"))){
            var msg = "";
            if(msg != "") {
                show_messages(msg, 'danger');
            } else {
                var data_form = $("form#form_chapter").serializeArray();
                jqxhr = $.post(
                    $( "form#form_chapter" ).attr("action"),
                    data_form
                );
                jqxhr.done(function(data){
                    if(data.list_chapter || data.form) {
                        if(data.errors){
                            get_form(data.form);
                        }else{
                            location.reload();
                        }
                    } else {
                        show_messages("{% trans 'You are no longer authenticated. Please log in again.' %}", 'danger', true);
                    }
                });
                jqxhr.fail(function($xhr) {
                    var data = $xhr.status+ " : " +$xhr.statusText;
                    show_messages("{% trans 'Error during recording.' %} " + "("+data+")<br/>"+"{% trans 'No data could be stored.' %}", 'danger');
                });
            }
        }else{
            show_messages("{% trans 'One or more errors have been found in the form.' %}", 'danger');
        }
    }
});

$(document).on("submit", "form#form_chapter_import", function (e) {
	$(this).show();
    e.preventDefault();
    var jqxhr= '';
    var action = $(this).find('input[name=action]').val();
    if (action == "import") {
    	var data_form = $("form#form_chapter_import").serializeArray();
    	jqxhr = $.post(
    		$("form#form_chapter_import").attr("action"),
    		data_form
    	);
    	jqxhr.done(function(data){
	        if(data.list_chapter || data.form) {
	            if(data.errors){
	                get_form(data.form);
	            }else{
	                refresh_list_and_player(data);
	                manageResize();
	            }
	        } else {
	            show_messages("{% trans 'You are no longer authenticated. Please log in again.' %}", 'danger', true);
	        }
	    });
	    jqxhr.fail(function($xhr) {
	        var data = $xhr.status+ " : " +$xhr.statusText;
	        show_messages("{% trans 'Error during recording.' %} " + "("+data+")<br/>"+"{% trans 'No data could be stored.' %}", 'danger');
	    });
    }
});

$(document).on("submit", "form#form_new", function (e) {
    e.preventDefault();
    var jqxhr= '';
    var action = $(this).find('input[name=action]').val();
    if (action == "new") {
        $('form#form_new').hide();
        $('form.form_modif').hide();
        $('form.form_delete').hide();
        manageResize();
        var elt = $(this).parents('tr');
        jqxhr = $.post( window.location.href, {"action":"new"} );
        jqxhr.done(function(data){
            if(data.indexOf("form_chapter")==-1) {
                show_messages("{% trans 'You are no longer authenticated. Please log in again.' %}", 'danger', true);
            } else {
                get_form(data);
                elt.addClass('info');
            }
        });
        jqxhr.fail(function($xhr) {
            var data = $xhr.status+ " : " +$xhr.statusText;
            show_messages("{% trans 'Error getting form.' %} " + "("+data+")"+ "{% trans 'The form could not be recovered.'%}", 'danger');
            $('form.form_modif').show();
            $('form.form_delete').show();
            $('form#form_new').show();
            $('#form_chapter').html("");
            manageResize();
        });
    }
});

$(document).on("submit", "form.form_modif", function (e) {
    e.preventDefault();
    var jqxhr= '';
    var action = $(this).find('input[name=action]').val();
    if (action == "modify") {
        $('form#form_new').hide();
        $('form.form_modif').hide();
        $('form.form_delete').hide();
        manageResize();
        var elt = $(this).parents('tr');
        var id = $(this).find('input[name=id]').val();
        jqxhr = $.post( window.location.href, {"action": "modify", "id": id });
        jqxhr.done(function(data) {
            if(data.indexOf("form_chapter") == -1) {
                show_messages("{% trans 'You are no longer authenticated. Please log in again.' %}", 'danger', true);
            } else {
                get_form(data);
                elt.addClass('info');
            }
        });
        jqxhr.fail(function($xhr) {
            var data = $xhr.status+ " : " +$xhr.statusText;
            show_messages("{% trans 'Error getting form.' %} " + "("+data+")"+ "{% trans 'The form could not be recovered.'%}", 'danger');
            $('form.form_modif').show();
            $('form.form_delete').show();
            $('form#form_new').show();
            $('#form_chapter').html("");
            manageResize();
        });
    }
});

$(document).on("submit", "form.form_delete", function (e) {
    e.preventDefault();
    var jqxhr= '';
    var action = $(this).find('input[name=action]').val();
    if(action == "delete") {
        var deleteConfirm = confirm( "{% trans 'Are you sure you want to delete this chapter?' %}");
        if (deleteConfirm){
            var id = $(this).find('input[name=id]').val();
            jqxhr = $.post( window.location.href, {"action":"delete", "id": id });
            jqxhr.done(function(data){
                if(data.list_chapter) {
                    refresh_list_and_player(data);
                } else {
                    show_messages("{% trans 'You are no longer authenticated. Please log in again.' %}", 'danger', true);
                }
            });
            jqxhr.fail(function($xhr) {
                var data = $xhr.status+ " : " +$xhr.statusText;
                show_messages("{% trans 'Error during deletion.' %} " + "("+data+")<br/>"+"{% trans 'No data could be deleted.' %}", 'danger');
            });
        }
    }
});

/*** Refreshes the player with updates and shows the list of enrichments ***/
function refresh_list_and_player(data){
    delete videojs.players['player_video']
    $("#form_chapter").html("");
    $('form#form_new').show();
    $("span#chapter_player").html(data.player);
    $("span#list_chapter").html(data.list_chapter);
    loadVideo();
};
/*** Verify if value of field respect form field ***/
function verify_start_title_items(){
    if ( document.getElementById("id_title").value == "" || document.getElementById("id_title").value.length < 2 || document.getElementById("id_title").value.length > 100 ) {
        $("input#id_title")
            .before("<span class='form-help-inline'>&nbsp;&nbsp;{% trans 'Please enter a title from 2 to 100 characters.' %} </span>")
            .parents('div.form-group').addClass('has-error');
    }
    if ( document.getElementById("id_time_start").value == "" || document.getElementById("id_time_start").value < 0 || document.getElementById("id_time_start").value >= video_duration || document.getElementById("id_time_start").value >= document.getElementById("id_time_end").value ) {
        $("input#id_time_start")
            .before("<span class='form-help-inline'>&nbsp;&nbsp;{% trans 'Please enter a correct start field between 0 and' %} " + (video_duration -1) + "</span>")
            .parents('div.form-group').addClass('has-error');
    }
    if ( document.getElementById("id_time_end").value == "" || document.getElementById("id_time_end").value <= 0 || document.getElementById("id_time_end").value >= video_duration || document.getElementById("id_time_end").value <= document.getElementById("id_time_start").value ) {
    	$("input#id_time_end")
    		.before("<span class='form-help-inline'>&nbsp;&nbsp;{% trans 'Please enter a correct end field between 1 and' %} " + (video_duration - 1) + "</span>")
    		.parents('div.form-group').addClass('has-error');
    }
};

function overlaptest(){
    var new_start = parseInt(document.getElementById("id_time_start").value);
  	var new_end = parseInt(document.getElementById("id_time_end").value);
  	var id = parseInt(document.getElementById("id_chapter").value);
    var msg = "";
    $('ul#chapters li').each(function() {
        if ((id != $(this).attr('data-id')) && new_start == $(this).attr('data-start')) {
            var text = "{% trans 'The chapter' %}  "+ '"' +$(this).attr('data-title')+'"'+ "  {% trans 'starts at the same time.' %}";
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

function get_form(data) {
    $("#form_chapter").hide().html(data).fadeIn();
    $("input#id_time_start")
        .before("&nbsp;<span class='getfromvideo pull-right' style='margin:0;margin-bottom:4px'><a id='getfromvideo_start' class='btn btn-info btn-sm'>{% trans 'Get time from the player'%}</a><span class='timecode' style='font-size: 12px;'>&nbsp;</span></span>");
    $("input#id_time_end")
        .before("&nbsp;<span class='getfromvideo pull-right' style='margin:0;margin-bottom:4px'><a id='getfromvideo_end' class='btn btn-info btn-sm'>{% trans 'Get time from the player'%}</a><span class='timecode' style='font-size: 12px;'>&nbsp;</span></span>");
};

$(document).on('change','input#id_time_start',function() {
    $(this).parent().find("span.getfromvideo span.timecode").html(" "+parseInt($(this).val()).toHHMMSS());
});
$(document).on('change','input#id_time_end',function() {
    $(this).parent().find("span.getfromvideo span.timecode").html(" "+parseInt($(this).val()).toHHMMSS());
});

$(document).on('click','#page-video span.getfromvideo a',function(e) {
    e.preventDefault();
    if(!(typeof player === 'undefined')) {
        if($(this).context.id == "getfromvideo_start"){
            $("input#id_time_start").val(parseInt(player.currentTime()));
            $("input#id_time_start").trigger('change');
        }
        if($(this).context.id == "getfromvideo_end"){
            $("input#id_time_end").val(parseInt(player.currentTime()));
            $("input#id_time_end").trigger('change');
        }
    }
});