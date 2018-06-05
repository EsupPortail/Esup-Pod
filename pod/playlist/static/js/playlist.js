const table = $('#table_list_videos')[0];

var showalert = function(message, alerttype) {
    $('body').append('<div id="formalertdiv" class="alert ' + alerttype + ' alert-dismissible fade show" role="alert">' + message + '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button></div>');
    setTimeout(function() { $("#formalertdiv").remove(); }, 5000);
};

var ajaxfail = function(data) {
    showalert('Error getting form. (' + data + ') The form could not be recovered.', 'alert-danger');
};

$('.position-up').on('click', function() {
	var row = $(this).parents('tr:first');
	var currentposition = row.find('.video-position');
	var oldposition = row.prev().find('.video-position');
	if (currentposition.text() > 1) {
		currentposition.text(parseInt(currentposition.text()) - 1);
		oldposition.text(parseInt(oldposition.text()) + 1);
	}
	row.insertBefore(row.prev());
});

$('.position-down').on('click', function() {
	var row = $(this).parents('tr:first');
	var currentposition = row.find('.video-position');
	var oldposition = row.next().find('.video-position');
	if (parseInt(currentposition.text()) < table.rows.length - 1) {
		currentposition.text(parseInt(currentposition.text()) + 1);
		oldposition.text(parseInt(oldposition.text()) - 1);
	}
	row.insertAfter(row.next());
});

$('.position-delete').on('click', function() {
	var slug = $(this).parents('tr:first').find('.video-title').attr('data-slug');
	var jqxhr = $.ajax({
		method: 'POST',
		url: window.location.href,
		data: {'action': 'delete', 'video': slug, 'csrfmiddlewaretoken': $('#playlist_form').find('input[name="csrfmiddlewaretoken"]').val()},
		dataType: 'html'
	});
	jqxhr.done(function(data) {
		if (data.indexOf('success') == -1) {
			showalert('You are no longer authenticated. Please log in again.', 'alert-danger');
		} else {
			showalert(JSON.parse(data).success, 'alert-success');
			window.location.reload();
		}
	});
	jqxhr.fail(function($xhr) {
		var data = $xhr.status + ' : ' + $xhr.statusText;
		ajaxfail(data);
	});
});

$('#save-position').on('click', function() {
	var videos = {};
	for (let i = 1; i < table.rows.length; i++) {
		var slug = table.rows[i].children[1].attributes['data-slug'].value;
		var pos = table.rows[i].children[4].innerHTML;
		videos[slug] = pos;
	}
	data = JSON.stringify(videos);
	var jqxhr = $.ajax({
		method: 'POST',
		url: window.location.href,
		data: {'action': 'move', 'videos': data, 'csrfmiddlewaretoken': $('#playlist_form').find('input[name="csrfmiddlewaretoken"]').val()},
		dataType: 'html'
	});
	jqxhr.done(function(data) {
		if (data.indexOf('success') == -1) {
			showalert('You are no longer authenticated. Please log in again.', 'alert-danger');
		} else {
			showalert(JSON.parse(data).success, 'alert-success');
		}
	});
	jqxhr.fail(function($xhr) {
		var data = $xhr.status + ' : ' + $xhr.statusText;
		ajaxfail(data);
	});
});

$(window).ready(function() {
	$('.playlist-delete').on('click', function() {
		if (confirm('Do you want to delete this playlist ?')) {
			var id = $(this).parents('div:first').attr('data-id');
			var jqxhr = $.ajax({
				method: 'POST',
				url: window.location.href,
				data: {'playlist': id, 'csrfmiddlewaretoken': $(this).parents('div:first').find('input[name="csrfmiddlewaretoken"]').val()},
				dataType: 'html'
			});
			jqxhr.done(function(data) {
				if (data.indexOf('success') == -1 || data.indexOf('fail') == -1) {
					showalert('You are no longer authenticated. Please log in again.', 'alert-danger');
				} else {
					response = JSON.parse(data);
					if (response.success) {
						showalert(data.success, 'alert-success');
						window.location.reload();
					} else {
						showalert(data.fail, 'alert-danger');
					}
				}
			});
			jqxhr.fail(function($xhr) {
				var data = $xhr.status + ' : ' + $xhr.statusText;
				ajaxfail(data);
			});
		}
	});
});
