$(window).on('load', function() {
	$('li.contenuTitre').css('display', 'none');

	var accordeon_head = $('#accordeon li a.title');
	var accordeon_body = $('#accordeon li.contenuTitre');

	accordeon_head.first().addClass('active').parent().next().slideDown('normal');

	// Click on .titre
	accordeon_head.on('click', function(event) {
		event.preventDefault();
		if ($(this).attr('class') != 'title active') {
			$(this).parent().next().slideToggle('normal');
			$(this).addClass('active');
		} else if ($(this).attr('class') == 'title active') {
			$(this).parent().next().slideUp('normal');
			$(this).removeClass('active');
		}
	});
});

// Video form
var num = 0;
var name = '';

// RESET
$(document).on('reset', '#accordeon form.completion', function(event) {
	var id_form = $(this).attr('id');
	var name_form = id_form.substring(5, id_form.length);
	var form_new = 'form_new_' + name_form;
	var list = 'list_' + name_form
	$('span#' + id_form).html('');
	$('form#' + form_new).show();
	$('form').show();
	$('a.title').css('display', 'initial');
	$('table tr').removeClass('info');
	$('#fileModal_id_document').remove();
	$('#fileModal_id_src').remove();
});

function show_form(data, form) {
	$('#'+form).hide().html(data).fadeIn();
};

var ajaxfail = function(data, form) {
	showalert(gettext('Error getting form.') + ' (' + data + ') ' + gettext('The form could not be recovered.'), 'alert-danger');
};

//SUBMIT

$(document).on('submit', '#accordeon form.completion', function(e) {
	e.preventDefault();
	var jqxhr = '';
	var exp = /_([a-z]*)\s?/g;
	var id_form = $(this).attr('id');
	var name_form = '';
	var result_regexp = '';
	if (id_form == undefined) {
		var form_class = $(this).find('input[type=submit]').attr('class');
		result_regexp = exp.exec(form_class);
		name_form = result_regexp[1];
	} else {
		result_regexp = id_form.split(exp);
		name_form = result_regexp[result_regexp.length - 2];
	}
	var form = 'form_' + name_form;
	var list = 'list_' + name_form;
	var action = $(this).find('input[name=action]').val();
	sendandgetform(this, action, name_form, form, list);
});


var sendandgetform = function(elt, action, name, form, list) {
	var href = $(elt).attr('action');
	if (action == 'new' || action == 'form_save_new') {
		$('.info-card').hide();
		$('#' + name + '-info').show();
		var jqxhr = $.ajax({
			method: 'POST',
			url: window.location.origin + href,
			data: {'action': action, 'csrfmiddlewaretoken': $(elt).find('input[name="csrfmiddlewaretoken"]').val()},
			dataType: 'html'
		});
		jqxhr.done(function(data) {
			if (data.indexOf(form) == -1) {
				showalert(gettext('You are no longer authenticated. Please log in again.', 'alert-danger'));
			} else {
				show_form(data, form);
			}
		});
		jqxhr.fail(function($xhr) {
			var data = $xhr.status + ' : ' + $xhr.statusText;
			ajaxfail(data);
			$('form.form_modif').show();
			$('form.form_delete').show();
			$('form.form_new').show();
			$('#' + form).html('');
		});
		$('form.form_new').hide();
		$('form.form_modif').hide();
		$('form.form_delete').hide();
		$('a.title').css('display', 'none');
		hide_others_sections(name);
	}
	if (action == 'modify' || action == 'form_save_modify') {
		var id = $(elt).find('input[name=id]').val();
		var jqxhr = $.ajax({
			method: 'POST',
			url: window.location.origin + href,
			data: {'action': action, 'id': id, 'csrfmiddlewaretoken': $(elt).find('input[name="csrfmiddlewaretoken"]').val()},
			dataType: 'html'
		});
		jqxhr.done(function(data) {
			if (data.indexOf(form) == -1) {
				showalert(gettext('You are no longer authenticated. Please log in again.', 'alert-danger'));
			} else {
				show_form(data, form);
			}
		});
		jqxhr.fail(function($xhr) {
			var data = $xhr.status + ' : ' + $xhr.statusText;
			ajaxfail(data, form);
			$('form.form_modif').show();
			$('form.form_delete').show();
			$('form.form_new').show();
			$('#' + form).html('');
		});
		$('form.form_new').hide();
		$('form.form_modif').hide();
		$('form.form_delete').hide();
		$('a.title').css('display', 'none');
		hide_others_sections(name);
	}
	if (action == 'delete') {
		var deleteConfirm = '';
		if (name == 'track') {
			deleteConfirm = confirm(gettext('Are you sure you want to delete this file ?'));
		} else if (name == 'contributor') {
			deleteConfirm = confirm(gettext('Are you sure you want to delete this contributor ?'));
		} else if (name == 'document') {
			deleteConfirm = confirm(gettext('Are you sure you want to delete this document ?'));
		} else if (name == 'overlay') {
			deleteConfirm = confirm(gettext('Are you sure you want to delete this overlay ?'));
		}
		if (deleteConfirm) {
			var id = $(elt).find('input[name=id]').val();
			jqxhr = $.ajax({
				method: 'POST',
				url: window.location.origin + href,
				data: {'action': action, 'id': id, 'csrfmiddlewaretoken': $(elt).find('input[name="csrfmiddlewaretoken"]').val()},
				dataType: 'html'
			});
			jqxhr.done(function(data) {
				data = JSON.parse(data);
				if (data.list_data) {
					refresh_list(data, form, list);
				} else {
					showalert(gettext('You are no longer authenticated. Please log in again.', 'alert-danger'));
				}
			});
			jqxhr.fail(function($xhr) {
				var data = $xhr.status + ' : ' + $xhr.statusText;
				ajaxfail(data, form);
			});
		}
	}
	if (action == 'save') {
		$('.form-help-inline').parents('div.form-group').removeClass('has-error');
		$('.form-help-inline').remove();
		if (verify_fields()) {
			var data_form = $('form#' + form).serialize();
			var jqxhr = $.ajax({
				method: 'POST',
				url: window.location.origin + href,
				data: data_form,
				dataType: 'html'
			});
			jqxhr.done(function(data) {
				data = JSON.parse(data);
				if (data.list_data || data.form) {
					if (data.errors) {
						$('#fileModal_id_src').remove();
						show_form(data.form, form);
					} else {
						refresh_list(data, form, list);
						$(window).scrollTop(100);
						showalert(gettext('Changes have been saved.'), 'alert-info');
					}
				} else {
					showalert(gettext('You are no longer authenticated. Please log in again.'), 'alert-danger');
				}
			});
			jqxhr.fail(function($xhr) {
				var data = $xhr.status + ' : ' + $xhr.statusText;
				ajaxfail(data, form);
			});
			$('form.form_new').hide();
			$('form.form_modif').hide();
			$('form.form_delete').hide();
		}
	}
	feather.replace({ class: 'align-bottom'});
}

// Hide others sections
function hide_others_sections(name_form) {
	var sections = $('a.title.active').not('a[id="section_' + name_form + '"]');
	if (sections.length > 0) {
		sections.parent().next().slideUp('normal');
		sections.removeClass('active');
		var i;
		for ( i = 0; i < sections.length; i++) {
			var section = sections[i];
			var text = section.text;
			var name_section = '\'' + text.replace(/\s/g, '') + '\''
			section.title = gettext('Display') + " " + name_section + " " + gettext('section');
			section.firstElementChild.className = 'glyphicon glyphicon-chevron-down';
		}
	}
}

// Refreshes the list
function refresh_list(data, form, list) {
	$('#' + form).html('');
	$('form.form_new').show();
	$('form').show();
	$('a.title').css('display', 'initial');
	$('span#enrich_player').html(data.player);
	$('span#' + list).html(data.list_data);
}

// Check fields
function verify_fields(form) {
	var error = false;
	if (form == 'form_contributor') {
		if ((document.getElementById('id_name').value == '') || (document.getElementById('id_name').value.length < 2) || (document.getElementById('id_name').length > 200)) {
			$('input#id_name')
				.before("<span class='form-help-inline'>&nbsp;&nbsp;" + gettext('Please enter a name from 2 to 100 caracteres.') + "</span>")
				.parents('div.form-group').addClass('has-error');
			error = true;
		}
		if (document.getElementById('id_weblink').value.length >= 200) {
			$('input#id_weblink')
				.before("<span class='form-help-inline'>&nbsp;&nbsp;" + gettext('You cannot enter a weblink with more than 200 caracteres.') + "</span>")
				.parents('div.form-group').addClass('has-error');
			error = true;
		}
		if (document.getElementById('id_role').value == '') {
			$('select#id_role')
				.before("<span class='form-help-inline'>&nbsp;&nbsp;" + gettext('Please enter a role.') + "</span>")
				.parents('div.form-group').addClass('has-error');
			error = true;
		}
		var id = parseInt(document.getElementById('id_contributor').value);
		var new_role = document.getElementById('id_role').value;
		var new_name = document.getElementById('id_name').value;
		$('#table_list_contributors tbody > tr').each(function() {
			if (id != $(this).find('input[name=id]')[0].value && $(this).find('td[class=contributor_name]')[0].innerHTML == new_name && $(this).find('td[class=contributor_role]')[0].innerHTML == new_role) {
				var text = gettext('There is already a contributor with this same name and role in the list.');
				showalert(text, 'alert-danger');
				error = true;
			}
		});
	} else if (form == 'form_track') {
		var element = document.getElementById('id_kind');
		var value = element.options[element.selectedIndex].value;
		var kind = element.options[element.selectedIndex].text;
		if (value != 'subtitles' && value != 'captions') {
			$('select#id_kind')
				.after("<span class='form-help-inline'>" + gettext('Please enter a correct kind.') + "</span>")
				.parents('div.form-group').addClass('has-error');
			error = true;
		}
		var element = document.getElementById('id_lang');
		var lang = element.options[element.selectedIndex].text;
		if (element.options[element.selectedIndex].value == '') {
			$('select#id_lang')
				.after("<span class='form-help-inline'>" + gettext('Please select a language.') + "</span>")
				.parents('div.form-group').addClass('has-error');
			error = true;
		}
		if (document.getElementById('id_src').value == '') {
			$('input#id_src')
				.after("<span class='form-help-inline'>" + gettext('Please specify a track file.') + "</span>")
				.parents('div.form-group').addClass('has-error');
			error = true;
		}
		if (document.getElementById('file-picker-path').innerHTML.split(' ')[1] != '(VTT)') {
			$('input#id_src')
				.after("<span class='form-help-inline'>" + gettext('Only .vtt format is allowed.') + "</span>")
				.parents('div.form-group').addClass('has-error');
			error = true;
		}
		var is_duplicate = false;
		$('#table_list_tracks > tbody > tr').each(function() {
			if (kind == $(this).find('td.subtitle_kind').text() && lang == $(this).find('td.subtitle_lang').text()) {
				is_duplicate = true;
				return false;
			}
		});
		if (is_duplicate) {
			$('input#id_src')
				.after("<br><span class='form-help-inline'>" + gettext('There is already a track with the same kind and language in the list.') + "</span>")
				.parents('div.form-group').addClass('has-error');
			error = true;
		}
	} else if (form == 'form_document') {
		if ($('img#id_document_thumbnail_img').attr('src') == '/static/icons/nofile_48x48.png') {
			$('img#id_document_thubmanil_img')
				.before("<span class='form-help-inline'>&nbsp;&nbsp;" + gettext('Please select a document.') + "</span>")
				.parents('div.form-group').addClass('has-error');
			error = true;
		}
	} else if (form == 'form_overlay') {
		var tags = /<script.+?>|<iframe.+?>/;
		if (tags.exec(document.getElementById('id_content').value) != null) {
			$('textarea#id_content')
				.before("<span class='form-help-inline'>&nbsp;&nbsp;" + gettext('Iframe and Script tags are not allowed.') + "</span>")
				.parents('div.form-group').addClass('has-error');
			error = true;
		}
	}
	return !error;
}

$('.new-contributor').on('click')