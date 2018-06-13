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
        if(link.indexOf('autoplay=true') <0){
                link = link.replace('is_iframe=true', 'is_iframe=true&autoplay=true');
            }

    } else if (link.indexOf('autoplay=true') >0) {
       link = link.replace('&autoplay=true', '');
    }
    // Autoplay
    if ($('#loop').is(':checked')) {
        if(link.indexOf('loop=true') <0){
                link = link.replace('is_iframe=true', 'is_iframe=true&loop=true');
            }

    } else if (link.indexOf('loop=true') >0) {
       link = link.replace('&loop=true', '');
    }
    $('#txtpartage').val(link);
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
             $('#txtpartage').val($('#txtpartage').val()+'?start='+parseInt(player.currentTime()));
             var valeur = $('#txtintegration').val();
             $('#txtintegration').val(valeur.replace('/?', '/?start=' + parseInt(player.currentTime())+'&'));
        }
        $('#txtposition').val(player.currentTime().toHHMMSS());
    }else{
         $('#txtpartage').val($('#txtpartage').val().replace(/(\?start=)\d+/, ''));
         $('#txtintegration').val($('#txtintegration').val().replace(/(start=)\d+&/, ''));
         $('#txtposition').val("");
    }
});

/*** USE TO SHOW THEME FROM CHANNELS ***/
var get_list = function(tab, level=0, tab_selected=[], tag_type="option", li_class='', attrs='', add_link=false, current="", channel="") {
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
        var count = Object.keys(child).length;
        if(count>0) {
            list += get_list(val.child, level+=1, tab_selected, tag_type, li_class, attrs, add_link, current, channel);
        }
    });
    return list;
}

/*** CHANNELS IN NAVBAR ***/
$("#list-channels .show-themes").mouseenter(function() {
    var str = get_list(listTheme["channel_"+$(this).data('id')], 0, [], tag_type="li", li_class="list-group-item", attrs='', add_link=true, current="", channel="");
    $(this).children('.list-group').html(str).show();
    $(this).addClass('list-group-item-info');
});

$("#list-channels .show-themes").mouseleave(function() {
    $(this).children('.list-group').html("").hide();
    $(this).removeClass('list-group-item-info');
});

$('#ownerboxnavbar').keyup(function() {
	if($(this).val() && $(this).val().length > 2) {
		var valThis = $(this).val().toLowerCase();
		var letter = valThis.charAt(0);
		var nbuser = listUser[letter].length;
		$("#accordion").html("");
		for(i=0; i<nbuser; i++) {
			var lastname = listUser[letter][i]["last_name"].toLowerCase();
			if(lastname.indexOf(valThis) != -1) 
				$("#accordion").append('<li><a href="'+urlvideos+'?owner='+listUser[letter][i]["username"]+'" title="">'+listUser[letter][i]["first_name"]+' '+listUser[letter][i]["last_name"]+' ('+listUser[letter][i]["username"]+')</a></li>');
		}
	} else {
		$("#accordion").html("");
	}
});
$(".showUser").on('click', function() {
	var letter = $(this).attr("data-target").toLowerCase();
	var nbuser = listUser[letter].length;
	$("#accordion").html("");
	for(i=0; i<nbuser; i++) {
		$("#accordion").append('<li><a href="'+urlvideos+'?owner='+listUser[letter][i]["username"]+'" title="">'+listUser[letter][i]["first_name"]+' '+listUser[letter][i]["last_name"]+' ('+listUser[letter][i]["username"]+')</a></li>');
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
/*** FORM THEME, NOTES AND USER PICTURE ***/
/** NOTES **/
$(document).on("submit", "#video_notes_form", function (e) {
    e.preventDefault();
    var data_form = $( "#video_notes_form" ).serializeArray();
    send_form_data($( "#video_notes_form" ).attr("action"), data_form, "show_form_notes", "post");
});
$(document).on("click", ".get_form_userpicture", function() {
	send_form_data($(this).data('url'), {}, "append_picture_form", "get");
});
$(document).on('hidden.bs.modal', '#userpictureModal', function (e) {
  $('#userpictureModal').remove();
});
$(document).on("submit", "#userpicture_form", function (e) {
    e.preventDefault();
    var data_form = $( "#userpicture_form" ).serializeArray();
	send_form_data($( "#userpicture_form" ).attr("action"), data_form, "show_picture_form");
});
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
var show_form_notes = function(data) {
	$( "#video_notes_form" ).parent().html(data);
}
var show_form_theme_new = function(data) {
	if(data.indexOf(id_form)==-1) {
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
        $(".get_form_userpicture").html('<img src="'+$(data).find("#userpictureurl").val()+'" height="34" class="rounded" alt="">Change your picture');
    }
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
    var valThis = $(this).val().toLowerCase();
    var letter = valThis.charAt(0);
    var nbuser = listUser[letter].length;
    /*$("#accordion").html("");*/
    $("#collapseFilterOwner .added").prop('checked', false).remove();
    for(i=0; i<nbuser; i++) {
      var lastname = listUser[letter][i]["last_name"].toLowerCase();
      if(lastname.indexOf(valThis) != -1 && listUserChecked.indexOf(listUser[letter][i]["username"])==-1 ) {
        var chekboxhtml = '<div class="form-check added"><input class="form-check-input" type="checkbox" name="owner" value="'+listUser[letter][i]["username"]+'" id="id'+listUser[letter][i]["username"]+'"><label class="form-check-label" for="id'+listUser[letter][i]["username"]+'">'+listUser[letter][i]["first_name"]+' '+listUser[letter][i]["last_name"]+' ('+listUser[letter][i]["username"]+')</label></div>';
        $("#collapseFilterOwner").append(chekboxhtml);
      }
    }
  } else {
    $("#collapseFilterOwner .added").prop('checked', false).remove();
  }
});
/****** VIDEOS EDIT ******/
/** channel **/

var tab_initial = new Array();

$('#id_theme option:selected').each(function () {
    tab_initial.push($(this).val());
});

$('#id_theme option').remove();

$('#id_channel').change(function() {
    $('#id_theme option').remove();
    var tab = $(this).val();
    var str = "";
    for (var id in tab) {
        var chan = $("#id_channel option[value="+tab[id]+"]").text();
        str += get_list(listTheme["channel_"+tab[id]], 0, [], tag_type="option", li_class="", attrs='', add_link=false, current="", channel=chan+": ");
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
}
restricted_access();
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
          showalert(gettext("Errors appear in the form, please correct it"),"alert-danger");
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
