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

/** CSRF METHOD **/
function csrfSafeMethod(method) {
	return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
	crossDomain: false,
	beforeSend: function(xhr, settings) {
		if (!csrfSafeMethod(settings.type)) {
			xhr.setRequestHeader('X-CSRFToken', csrftoken)
		}
	}
});
var csrftoken = getCookie('csrftoken');

function getCookie(name) {
	var cookieValue = null;
	if (document.cookie && document.cookie != '') {
		var cookies = document.cookie.split(';');
		for (var i = 0; i < cookies.length; i++) {
			var cookie = jQuery.trim(cookies[i]);
			if (cookie.substring(0, name.length + 1) == (name + '=')) {
				cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
			}
		}
	}
	return cookieValue;
}