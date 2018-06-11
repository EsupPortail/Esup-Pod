
/*** USE TO SHOW THEME FROM CHANNELS ***/
var get_list = function(tab, level=0, tab_selected=[], tag_type="option", attrs='', add_link=false) {
    var list = ""
    var prefix = ""
    for(i=0;i<level;i++) prefix+="&nbsp;&nbsp;";
    if(level!=0) prefix+="|-";
    $.each(tab, function(i, val) {
        var title = add_link ? '<a href="'+val.url+'">'+val.title+'</a>' : val.title;
        var selected = $.inArray(i, tab_selected) > -1 ? "selected" : "";
        list += '<'+tag_type+' '+selected+' '+attrs+' value="'+i+'">'+prefix+" "+title+'</'+tag_type+'>';
        var child = val.child;
        var count = Object.keys(child).length;
        if(count>0) {
            list += get_list(val.child, level+=1, tab_selected, tag_type, attrs, add_link);
        }
    });
    return list;
}

/*** CHANNELS IN NAVBAR ***/
$("#list-channels .show-themes").mouseenter(function() {
    var str = get_list(listTheme["channel_"+$(this).data('id')], 0, [], "li", 'class="list-group-item"',true);
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
    TriggerAlertClose();
});

function TriggerAlertClose() {
    window.setTimeout(function () {
        $(".alert").fadeTo(1000, 0).slideUp(1000, function () {
            $(this).remove();
        });
    }, 5000);
}
/*** USER PICTURE ***/
$(document).on("click", ".get_form_userpicture", function() {
    jqxhr = $.get(
        $(this).data('url')
    );
    jqxhr.done(function(data){
        $('body').append(data);
        $('#userpictureModal').modal('show');
    });
    jqxhr.fail(function($xhr) {
        var data = $xhr.status+ " : " +$xhr.statusText;
        showalert("Error during recording." + "("+data+")<br/>"+"No data could be stored.", "alert-danger");
    });
});
$(document).on('hidden.bs.modal', '#userpictureModal', function (e) {
  $('#userpictureModal').remove();
});
$(document).on("submit", "#userpicture_form", function (e) {
    e.preventDefault();
    var jqxhr= '';
    var data_form = $( "#userpicture_form" ).serializeArray();
    jqxhr = $.post(
        $( "#userpicture_form" ).attr("action"),
        data_form
    );
    jqxhr.done(function(data){
        $( "#userpicture_form" ).html($(data).find("#userpicture_form").html());
        if($(data).find("#userpictureurl").val()) {
            $(".get_form_userpicture").html('<img src="'+$(data).find("#userpictureurl").val()+'" height="34" class="rounded" alt="">Change your picture');
        }
    });
    jqxhr.fail(function($xhr) {
        var data = $xhr.status+ " : " +$xhr.statusText;
        showalert("Error during recording." + "("+data+")<br/>"+"No data could be stored.", "alert-danger");
    });
});

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
