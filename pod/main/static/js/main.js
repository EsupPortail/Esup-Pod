/** FUNCTIONS **/

function linkTo_UnCryptMailto( s ) {
    location.href="mailto:"+window.atob(s);
}

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

// Edit the iframe and share link code
function writeInFrame() {
    // Iframe
    var str = $('#txtintegration').val();
    // Autoplay
    if ($('#autoplay').is(':checked')) {
            if(str.indexOf('autoplay=true') < 0){
                str = str.replace('is_iframe=true', 'is_iframe=true&autoplay=true');
            }
    } else if (str.indexOf('autoplay=true') > 0) {
        str = str.replace('&autoplay=true', '');
    }
    // Loop
    if ($('#loop').is(':checked')) {
            if(str.indexOf('loop=true') < 0){
                str = str.replace('is_iframe=true', 'is_iframe=true&loop=true');
            }
    } else if (str.indexOf('loop=true') > 0) {
        str = str.replace('&loop=true', '');
    }
    $('#txtintegration').val(str);

    // Share link
    var link = $('#txtpartage').val();
    // Autoplay
    if ($('#autoplay').is(':checked')) {
        if(link.indexOf('autoplay=true') < 0){
                if(link.indexOf('?') < 0) link = link+"?autoplay=true";
                else if (link.indexOf('loop=true') > 0 || link.indexOf('start=') > 0) link = link+"&autoplay=true";
                else link = link+"autoplay=true";
            }

    } else if (link.indexOf('autoplay=true') > 0) {
       link = link.replace('&autoplay=true', '').replace('autoplay=true&', '').replace('?autoplay=true', '?');
    }
    // Loop
    if ($('#loop').is(':checked')) {
        if(link.indexOf('loop=true') < 0){
                if(link.indexOf('?') < 0) link = link+"?loop=true";
                else if (link.indexOf('autoplay=true') > 0 || link.indexOf('start=') > 0) link = link+"&loop=true";
                else link = link+"loop=true"
            }

    } else if (link.indexOf('loop=true') > 0) {
       link = link.replace('&loop=true', '').replace('?loop=true&', '?').replace('?loop=true', '?');

    }

    //Remove ? to start when he's first
    if (link.indexOf('??') > 0) link = link.replace(/\?\?/, '?');

    $('#txtpartage').val(link);
    var img = document.getElementById("qrcode");
    img.src = "//chart.apis.google.com/chart?cht=qr&chs=200x200&chl=" + link;
}
$(document).on('change', '#autoplay', function() {
    writeInFrame();
});
$(document).on('change', '#loop', function() {
    writeInFrame();
});

$(document).on('change', "#displaytime", function(e) {
    if($('#displaytime').is(':checked')){
        if($('#txtpartage').val().indexOf('start')<0){
             $('#txtpartage').val($('#txtpartage').val()+'&start='+parseInt(player.currentTime()));
             if ($('#txtpartage').val().indexOf('??') > 0) $('#txtpartage').val($('#txtpartage').val().replace('??', '?'));
             var valeur = $('#txtintegration').val();
             $('#txtintegration').val(valeur.replace('/?', '/?start=' + parseInt(player.currentTime())+'&'));
        }
        $('#txtposition').val(player.currentTime().toHHMMSS());
    }else{
         $('#txtpartage').val($('#txtpartage').val().replace(/(\&start=)\d+/, '').replace(/(\start=)\d+/, '').replace(/(\?start=)\d+/, ''));

         $('#txtintegration').val($('#txtintegration').val().replace(/(start=)\d+&/, ''));
         $('#txtposition').val("");
    }

    //Replace /& => /?
    var link = $('#txtpartage').val();
    if ($('#txtpartage').val().indexOf('/&') > 0) link = link.replace('/&', '/?');
    $('#txtpartage').val(link);

    var img = document.getElementById("qrcode");
    img.src = "//chart.apis.google.com/chart?cht=qr&chs=200x200&chl="+$('#txtpartage').val();
});

/*** USE TO SHOW THEME FROM CHANNELS ***/
var get_list = function(tab, level, tab_selected, tag_type, li_class, attrs, add_link, current, channel, show_only_parent_themes=false) {
    level = level || 0;
    tab_selected = tab_selected || [];
    tag_type = tag_type || "option";
    li_class = li_class || '';
    attrs = attrs || '';
    add_link = add_link || false;
    current = current || false;
    channel = channel || "";
    var list = ""
    var prefix = ""
    for(i=0;i<level;i++) prefix+="&nbsp;&nbsp;";
    if(level!=0) prefix+="|-";
    $.each(tab, function(i, val) {
        var title = add_link ? '<a href="'+val.url+'">'+channel+' '+val.title+'</a>' : channel+' '+val.title;
        var selected = $.inArray(i, tab_selected) > -1 ? "selected" : "";
        var list_class = 'class="'+li_class;
        if(val.slug==current) list_class+=' list-group-item-info"';
        else list_class+='"';
        list += '<'+tag_type+' '+selected+' '+list_class+' '+attrs+' value="'+i+'" id="theme_'+i+'">'+prefix+" "+title+'</'+tag_type+'>';
        var child = val.child;
        var count =  Object.keys(child).length;
        if(count>0 && !show_only_parent_themes) {
            list += get_list(child, level+=1, tab_selected, tag_type, li_class, attrs, add_link, current, channel);
        }
    });
    return list;
}

/*** CHANNELS IN NAVBAR ***/

$('.collapsibleThemes').on('show.bs.collapse', function () {
  var str = get_list(listTheme["channel_"+$(this).data('id')], 0, [], tag_type="li", li_class="list-inline-item badge badge-primary-pod badge-pill", attrs='', add_link=true, current="", channel="", show_only_parent_themes=show_only_parent_themes);
  $(this).html('<ul class="list-inline p-1 border">'+str+'</ul>')
  //$(this).parents("li").addClass('list-group-item-light');
  $(this).parents("li").find('.chevron-down').attr('style', 'transform: rotate(180deg);');
})
$('.collapsibleThemes').on('hidden.bs.collapse', function () {
  // do something…
  //$(this).parents("li").removeClass('list-group-item-light');
  $(this).parents("li").find('.chevron-down').attr('style', '');
})
$('#ownerboxnavbar').keyup(function() {
	if($(this).val() && $(this).val().length > 2) {
		var searchTerm = $(this).val();
            $.ajax(
                {
                    type: "GET",
                    url: "/ajax_calls/search_user?term=" + searchTerm,
                    cache: false,
                    success: function (response) {
                        $("#accordion").html("");
                        response.forEach(elt => {
                            $("#accordion").append('<li><a href="'+urlvideos+'?owner='+elt.username+'" title="">'+elt.first_name+' '+elt.last_name+((!HIDE_USERNAME)?' ('+elt.username+')</a></li>': '</a></li>'));
                        })
                    }
                }
            );

	} else {
		$("#accordion").html("");
	}
});

/** MENU ASIDE **/
$(document).ready(function () {

    //when a group is shown, save it as the active accordion group
    $("#collapseAside").on('shown.bs.collapse', function () {
        Cookies.set('activeCollapseAside', "open");
        $(".collapseAside").html('<i data-feather="corner-left-up"></i><i data-feather="menu"></i>');
        feather.replace({ class: 'align-bottom'});
    });
    $("#collapseAside").on('hidden.bs.collapse', function () {
        Cookies.set('activeCollapseAside', "close");
        $(".collapseAside").html('<i data-feather="corner-left-down"></i><i data-feather="menu"></i>');
        feather.replace({ class: 'align-bottom'});
    });
    var last = Cookies.get('activeCollapseAside');
    //alert('last '+last);
    if (last != null && last=="close") {
        //show the account_last visible group
        $("#collapseAside").addClass("hide");
        $(".collapseAside").html('<i data-feather="corner-left-down"></i><i data-feather="menu"></i>');
        feather.replace({ class: 'align-bottom'});
    } else {
        $("#collapseAside").addClass("show");
        $(".collapseAside").html('<i data-feather="corner-left-up"></i><i data-feather="menu"></i>');
        feather.replace({ class: 'align-bottom'});
    }
    if ($("#collapseAside").find("div").length == 0) {
    	$("#collapseAside").collapse('hide');
    }
    TriggerAlertClose();
});

function TriggerAlertClose() {
    window.setTimeout(function () {
        $(".alert").fadeTo(1000, 0).slideUp(1000, function () {
            $(this).remove();
        });
    }, 5000);
}
/*** FORM THEME USER PICTURE ***/
/** PICTURE **/
$(document).on("click", ".get_form_userpicture", function() {
	send_form_data($(this).data('url'), {}, "append_picture_form", "get");
});
$(document).on('hidden.bs.modal', '#userpictureModal', function (e) {
    console.log('remove modal');
    $('#userpictureModal').remove();
    $('#fileModal_id_userpicture').remove();
});
$(document).on("submit", "#userpicture_form", function (e) {
    e.preventDefault();
    var data_form = $( "#userpicture_form" ).serializeArray();
	send_form_data($( "#userpicture_form" ).attr("action"), data_form, "show_picture_form");
});
/** THEME **/
$(document).on("submit", "#form_theme", function (e) {
    e.preventDefault();
    var data_form = $( "#form_theme" ).serializeArray();
	send_form_data($( "#form_theme" ).attr("action"), data_form, "show_theme_form");
});
$(document).on('click', '#cancel_theme', function(){
    $('form.get_form_theme').show();
    show_form_theme("");
    $("#table_list_theme tr").removeClass('table-primary');
    window.scrollTo({
        top: parseInt($("#list_theme").offset().top),
        behavior: "smooth"
    });
});
$(document).on("submit", "form.get_form_theme", function (e) {
    e.preventDefault();
    var action = $(this).find('input[name=action]').val(); // new, modify and delete
    if(action == "delete"){
        var deleteConfirm = confirm(gettext("Are you sure you want to delete this element?"));
        if (deleteConfirm){
        	send_form_data(window.location.href, $(this).serializeArray(), "show_form_theme_"+action);
        }
    } else {
    	send_form_data(window.location.href, $(this).serializeArray(), "show_form_theme_"+action);
    }
});
/** VIDEO DEFAULT VERSION **/
$(document).on("change", "#video_version_form input[type=radio][name=version]", function (e) {
    $('#video_version_form').submit();
});
$(document).on("submit", "#video_version_form", function (e) {
    e.preventDefault();
    var data_form = $( "#video_version_form" ).serializeArray();
    send_form_data($( "#video_version_form" ).attr("action"), data_form, "result_video_form");
});
var result_video_form = function(data) {
    if(data.errors){
        showalert(gettext('One or more errors have been found in the form.'), "alert-danger");
    } else {
        showalert(gettext('Changes have been saved.'), 'alert-info');
    }
}

/** FOLDER **/

/** AJAX **/
var send_form_data = function(url,data_form, fct, method) {
  method = method || "post";
	var jqxhr= '';
	if(method=="post") jqxhr = $.post(url, data_form);
	else jqxhr = $.get(url);
    jqxhr.done(function(data){ window[fct](data); });
	jqxhr.fail(function($xhr) {
        var data = $xhr.status+ " : " +$xhr.statusText;
        showalert(gettext("Error during exchange") + "("+data+")<br/>"+gettext("No data could be stored."), "alert-danger");
    });
}

var show_form_theme_new = function(data) {
	if(data.indexOf("form_theme")==-1) {
        showalert(gettext('You are no longer authenticated. Please log in again.'), "alert-danger");
    } else {
        show_form_theme(data);
    }
}
var show_form_theme_modify = function(data) {
	if(data.indexOf("theme")==-1) {
        showalert(gettext('You are no longer authenticated. Please log in again.'), "alert-danger");
    } else {
        show_form_theme(data);
        var id = $(data).find('#id_theme').val();
        $("#theme_"+id).addClass('table-primary');
    }
}
var show_form_theme_delete = function(data) {
	if(data.list_element) {
        show_list_theme(data.list_element);
    } else {
        showalert(gettext('You are no longer authenticated. Please log in again.'), "alert-danger");
    }
}
var show_theme_form = function(data) {
	if(data.list_element || data.form) {
        if(data.errors){
            showalert(gettext('One or more errors have been found in the form.'), "alert-danger");
            show_form_theme(data.form);
        }else{
            show_form_theme("");
            $('form.get_form_theme').show();
            show_list_theme(data.list_element);
        }
    } else {
        showalert(gettext('You are no longer authenticated. Please log in again.'), "alert-danger");
    }
}
var show_picture_form = function(data) {
	$( "#userpicture_form" ).html($(data).find("#userpicture_form").html());
    if($(data).find("#userpictureurl").val()) {
        //$(".get_form_userpicture").html('<img src="'+$(data).find("#userpictureurl").val()+'" height="34" class="rounded" alt="">Change your picture');
        $("#navbarDropdown .userpicture").remove();
        $("#navbarDropdown .userinitial").hide();
        $("#navbarDropdown").removeClass('initials');
        $("#navbarDropdown").append(
            '<img src="'+$(data).find("#userpictureurl").val()+'" class="userpicture img-fluid rounded" alt="avatar">'
        );
        $('.get_form_userpicture').html($('.get_form_userpicture').children());
        $(".get_form_userpicture").append('&nbsp;'+gettext('Change your picture'));
    } else {
        $("#navbarDropdown .userpicture").remove();
        $("#navbarDropdown .userinitial").show();
        $("#navbarDropdown").addClass('initials');
        $('.get_form_userpicture').html($('.get_form_userpicture').children());
        $(".get_form_userpicture").html('&nbsp;'+gettext('Add your picture'));
    }
    $('#userpictureModal').modal('hide');
}
var append_picture_form = function(data) {
	$('body').append(data);
    $('#userpictureModal').modal('show');
}
function show_form_theme(data) {
    $("#div_form_theme").hide().html(data).fadeIn();
    if(data!="") $('form.get_form_theme').hide();
    window.scrollTo({
        top: parseInt($("#div_form_theme").offset().top),
        behavior: "smooth"
    });
}
function show_list_theme(data) {
    $("#list_theme").hide().html(data).fadeIn();
    //$('form.get_form_theme').show();
    window.scrollTo({
        top: parseInt($("#list_theme").offset().top),
        behavior: "smooth"
    });
}
/***** VIDEOS *****/
$('#ownerbox').keyup(function() {
  if($(this).val() && $(this).val().length > 2) {
    var searchTerm = $(this).val();
            $.ajax(
                {
                    type: "GET",
                    url: "/ajax_calls/search_user?term=" + searchTerm,
                    cache: false,
                    success: function (response) {
                        $("#collapseFilterOwner .added").each(function(index){
                            var c = $(this).find("input");
                            if(!c.prop("checked")){
                                $(this).remove();
                            }
                        })



                        response.forEach(elt => {
                            if (listUserChecked.indexOf(elt.username)==-1 && $("#collapseFilterOwner #id" + elt.username).length == 0) {
                                let username = HIDE_USERNAME?'':(' ('+elt.username+')');
                                var chekboxhtml = '<div class="form-check added"><input class="form-check-input" type="checkbox" name="owner" value="'+elt.username+'" id="id'+elt.username+'"><label class="form-check-label" for="id'+elt.username+'">'+elt.first_name+' '+elt.last_name+ username+'</label></div>';
                                $("#collapseFilterOwner").append(chekboxhtml);
                            }
                        })
                    }
                }
            );


  } else {
    $("#collapseFilterOwner .added").each(function(index){
        var c = $(this).find("input");
        if(!c.prop("checked")){
            $(this).remove();
        }
    })
  }
});
/****** VIDEOS EDIT ******/
/** channel **/

var tab_initial = new Array();

$('#id_theme option:selected').each(function () {
    tab_initial.push($(this).val());
});

$('#id_theme option').remove();

//$('#id_channel').change(function() {
// use click instead of change due to select2 usage : https://github.com/theatlantic/django-select2-forms/blob/master/select2/static/select2/js/select2.js#L1502
$('#id_channel').on('click', function (e) {
    $('#id_theme option').remove();
    var tab_channel_selected = $(this).val();
    var str = "";
    for (var id in tab_channel_selected) {
        var chan = $("#id_channel option[value="+tab_channel_selected[id]+"]").text();
        str += get_list(listTheme["channel_"+tab_channel_selected[id]], 0, [], tag_type="option", li_class="", attrs='', add_link=false, current="", channel=chan+": ");
    }
    $('#id_theme').append(str);
});
$("#id_channel option:selected").each(function () {
    var str = get_list(listTheme["channel_"+$(this).val()], 0, tab_initial, tag_type="option", li_class="", attrs='', add_link=false, current="");
    $('#id_theme').append(str);
});

/** end channel **/
/*** Copy to clipboard ***/
$('#btnpartageprive').click(function() {
      var copyText = document.getElementById("txtpartageprive");
      copyText.select();
      document.execCommand("copy");
      showalert(gettext("text copied"),"alert-info");
  });

/** Restrict access **/
/** restrict access to group */
$("#id_is_restricted").change(function () {
    restrict_access_to_groups();
})
var restrict_access_to_groups = function () {
    if ($('#id_is_restricted').prop("checked")) {
        $("#id_restrict_access_to_groups").parents(".restricted_access").show();
    } else {
        $("#id_restrict_access_to_groups option:selected").prop("selected", false);
        $("#id_restrict_access_to_groups").parents(".restricted_access").hide();
    }
}
$('#id_is_draft').change(function(){
    restricted_access();
});
var restricted_access = function() {
    if($('#id_is_draft').prop( "checked" )){
        $('.restricted_access').addClass('hide');
        $('.restricted_access').removeClass('show');
        $("#id_password").val('');
        $("#id_restrict_access_to_groups option:selected").prop("selected", false);
        $("#id_is_restricted").prop( "checked", false );
    } else {
        $('.restricted_access').addClass('show');
        $('.restricted_access').removeClass('hide');
    }
    restrict_access_to_groups();
}
restricted_access();
//restrict_access_to_groups();

/** end restrict access **/
/*** VALID FORM ***/
(function() {
  'use strict';
  window.addEventListener('load', function() {
    // Fetch all the forms we want to apply custom Bootstrap validation styles to
    var forms = document.getElementsByClassName('needs-validation');
    // Loop over them and prevent submission
    var validation = Array.prototype.filter.call(forms, function(form) {
      form.addEventListener('submit', function(event) {
        if (form.checkValidity() === false) {
          window.scrollTo($(form).scrollTop(), 0);
          showalert(gettext("Errors appear in the form, please correct them"),"alert-danger");
          event.preventDefault();
          event.stopPropagation();
        } else {
            if($(form).data("morecheck")) {
                window[$(form).data("morecheck")](form, event);
            }
        }
        form.classList.add('was-validated');
      }, false);
    });
  }, false);
})();
/*** VIDEOCHECK FORM ***/
var videocheck = function(form,event) {
    var fileInput = $('#id_video');
    if(fileInput.get(0).files.length){
        var fileSize = fileInput.get(0).files[0].size;
        var fileName = fileInput.get(0).files[0].name;
        var extension = fileName.substring(fileName.lastIndexOf('.')+1).toLowerCase();
        if(listext.indexOf(extension) !== -1) {
            if(fileSize>video_max_upload_size){
                window.scrollTo($("#video_form").scrollTop(), 0);
                showalert(gettext("The file size exceeds the maximum allowed value :")+" "+VIDEO_MAX_UPLOAD_SIZE+" Go.","alert-danger");
                event.preventDefault();
                event.stopPropagation();
            } else {
                $("#video_form fieldset").hide();
                $("#video_form button").hide();
                $("#js-process").show();
                window.scrollTo($("#js-process").scrollTop(), 0);
                if(!show_progress_bar(form)) {
                    event.preventDefault();
                    event.stopPropagation();
                }
            }
        } else {
            window.scrollTo($("#video_form").scrollTop(), 0);
            showalert(gettext("The file extension not in the allowed extension :")+" "+listext+".","alert-danger");
            event.preventDefault();
            event.stopPropagation();
        }
    }
}

/***** SHOW ALERT *****/
var showalert = function(message,alerttype) {
    $('body').append('<div id="formalertdiv" class="alert ' +  alerttype + ' alert-dismissible fade show"  role="alert">'+message+'<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button></div>');
    setTimeout(function() { $("#formalertdiv").remove(); }, 5000);
};

function show_messages(msgText, msgClass, loadUrl) {
	var $msgContainer = $('#show_messages');
	var close_button = '';
	msgClass = typeof msgClass !== 'undefined' ? msgClass : 'warning';
	loadUrl = typeof loadUrl !== 'undefined' ? loadUrl : false;

	if (!loadUrl) {
		close_button = '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button>';
	}

	var $msgBox = $('<div>', {
		'class': 'alert alert-' + msgClass + ' alert-dismissable fade in',
		'role': 'alert',
		'html': close_button + msgText
	});
	$msgContainer.html($msgBox);

	if (loadUrl) {
		$msgBox.delay(4000).fadeOut(function() {
			if (loadUrl) {
				window.location.reload();
			} else {
				window.location.assign(loadUrl);
			}
		});
	} else if ( msgClass === 'info' || msgClass === 'success') {
		$msgBox.delay(3000).fadeOut(function() {
			$msgBox.remove();
		});
	}
}
