$(window).on('load', function() {
	manageResize('contributor');
	manageResize('track');
	manageResize('document');
	manageResize('overlay');
	$('li.contenuTitre').css('display', 'none');

	var accordeon_head = $('#accordeon li a.title');
	var accordeon_body = $('#accordeon li.contenuTitre');

	accordeon_head.first().addClass('active').parent().next().slideDown('normal');
	accordeon_head.first().children().removeClass('glyphicon glyphicon-chevron-down');
	accordeon_head.first().children().addClass('glyphicon glyphicon-chevron-up');

	// Click on .titre
	accordeon_head.on('click', function(event) {
		event.preventDefault();
		if ($(this).attr('class') != 'title active') {
			$(this).parent().next().slideToggle('normal');
			$(this).addClass('active');
			$(this).children().removeClass('glyphicon-chevron-down');
			$(this).children().addClass('glyphicon-chevron-up');
		} else if ($(this).attr('class') == 'title active') {
			$(this).parent().next().slideUp('normal');
			$(this).removeClass('active');
			$(this).children().removeClass('glyphicon-chevron-up');
			$(this).children().addClass('glyphicon-chevron-down');
		}
	});
});

// Table scroll
function manageResize(name_form) {
	var $table = '';
	$table = $('table#table_list_' + name_form + 's');
	var $body_cells = $table.find('tbody tr:first').children();
	var col_width;

	function resize() {
		col_width = $body_cells.map(function() {
			return $(this).width();
		}).get();
		$table.find('thead tr').children().each(function(i, v) {
			$(v).width(col_width[i]);
		});
	};
	resize();
}

// Video form
var num = 0;
var name = '';

// RESET
$(document).on('reset', '#page-video form', function(event) {
	var id_form = $(this).attr('id');
	var name_form = id_form.substring(5, id_form.length);
	var form_new = 'form_new_' + name_form;
	var list = 'list_' + name_form
	$('span#' + id_form).html('');
	$('form#' + form_new).show();
	$('form').show();
	$('a.title').css('display', 'initial');
	$('table tr').removeClass('info');
	manageResize(name_form);
});

//SUBMIT
$(document).on('submit', '#page-video form', function(event) {
	event.preventDefault();
	$('form').show();
	var jqxhr = '';
	var action = $(this).find('input[name=action]').val();
	var class_form = $(this).attr('class');
	var id_form = $(this).attr('id');
	var form = '';
	var list = '';
	var name_form = '';
	var exp = /_([a-z]*)\s?/g;
	var result_regexp = '';

	if (id_form == undefined) {
		var form_class = $(this).find('input[type=submit]').attr('class');
		result_regexp = exp.exec(form_class);
		name_form = result_regexp[1]
	} else {
		result_regexp = id_form.split(exp);
		name_form = result_regexp[result_regexp.length - 2];
	}
	form = 'form_' + name_form;
	list = 'list_' + name_form;
	var href = $(this).attr('action')
	if (action == 'modify' || action == 'new') {
		$('form.form_new').hide();
		$('form.form_modif').hide();
		$('form.form_delete').hide();
		$('a.title').css('display', 'none');
		hide_others_sections(name_form);
		var elt = $(this).parents('tr');
		//$('#' + form).html(ajax_image);
		if (action == 'modify') {
			var id = $(this).find('input[name=id]').val();
			jqxhr = $.post(
				window.location.origin + href,
				{'action': 'modify', 'id': id}
			);
		} else {
			jqxhr = $.post(
				window.location.origin + href,
				{'action': 'new'}
			);
			$('.info-card').hide();
			$('#'+name_form+'-info').show();
		}
		jqxhr.done(function(data) {
			if (data.indexOf(form) == 1) {
				show_messages("{% trans 'You are no longer authenticated. Please log in again.' %}", 'danger', true);
			} else {
				get_form(data, form);
				elt.addClass('info');
			}
		});
		jqxhr.fail(function($xhr) {
			var data = $xhr.status + ' : ' + $xhr.statusText;
			show_messages("{% trans 'Error getting form.' %} (" + data + ") {% trans 'The form could not be recovered.' %}", 'danger');
			$('form.form_modif').show();
			$('form.form_delete').show();
			$('form.form_new').show();
			$('#' + form).html('');
		});
	} else if (action == 'delete') {
		var deleteConfirm = '';
		if (name_form == 'track') {
			deleteConfirm = confirm("{% trans 'Are you sure you want to delete this file ?' %}");
		} else if (name_form == 'contributor') {
			deleteConfirm = confirm("{% trans 'Are you sure you want to delete this contributor ? %}");
		} else if (name_form == 'document') {
			deleteConfirm = confirm("{% trans 'Are you sure you want to delete this document ? %}");
		} else if (name_form == 'overlay') {
			deleteConfirm = confirm("{% trans 'Are tou sure you want to delete this overlay ? %}");
		}
		if (deleteConfirm) {
			var id = $(this).find('input[name=id]').val();
			jqxhr = $.post(
				window.location.origin + href,
				{'action': 'delete', 'id': id}
			);
			jqxhr.done(function(data) {
				if (data.list_data) {
					refresh_list(data, form, list);
					manageResize(name_form);
				} else {
					show_messages("{% trans 'You are no longer authenticated. Please log in again' %}", 'danger', true);
				}
			});
			jqxhr.fail(function($xhr) {
				var data = $xhr.status + ' : ' + $xhr.statusText;
				show_messages("{% trans 'Error during deletion.' %} (" + data + ") {% trans 'No data could be deleted.' %}", 'danger');
			});
		}
	} else if (action == 'save') {
		$('form.form_new').hide();
		$('form.form_modif').hide();
		$('form.form_delete').hide();
		$('.form-help-inline').parents('div.form-group').removeClass('has-error');
		$('.form-help-inline').remove();
		msg = verify_fields(form);
		if (!($('span').hasClass('form-help-inline'))) {
			if(msg != '') {
				show_messages(msg, 'danger')
			} else {
				var data_form = $('form#' + form).serializeArray();
				var href = $('form#' + form).attr('action');
				jqxhr = $.post(
					window.location.origin + href,
					data_form
				);
				jqxhr.done(function(data) {
					if (data.list_data || data.form) {
						if (data.errors) {
							get_form(data.form, form);
						} else {
							refresh_list(data, form, list);
							if (name_form != 'contributor') {
								$('span#' + form).unwrap();
								$('span#' + list).unwrap();
							}
							manageResize(name_form);
							$(window).scrollTop(100);
							show_messages("{% trans 'Changes have been saved.' %}", 'info');
						}
					} else {
						show_messages("{% trans 'You are no longer authenticated. Please log in again' %}", 'danger', true);
					}
				});
				jqxhr.fail(function($xhr) {
					var data = $xhr.status + ' : ' + $xhr.statusText;
					show_messages("{% trans 'Error during recording. (" + data + ") {% trans 'No data could be stored.' %}", 'danger');
				});
			}
		} else {
			show_messages("{% trans 'Errors found in the form, please correct it.' %}", 'danger');
		}
	}
});

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
			section.title = "{% trans 'Display " + name_section + " section' %}";
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

// Get form
function get_form(data, form) {
	$('#' + form).hide().html(data).fadeIn();
}

// Check fields
function verify_fields(form) {
	var msg = '';
	if (form == 'form_contributor') {
		if ((document.getElementById('id_name').value == '') || (document.getElementById('id_name').value.length < 2) || (document.getElementById('id_name').length > 200)) {
			$('input#id_name')
				.before("<span class='form-help-inline'>&nbsp;&nbsp;{% trans 'Please enter a name from 2 to 100 caracteres.' %}</span>")
				.parents('div.form-group').addClass('has-error');
		}
		if (document.getElementById('id_weblink').value.length >= 200) {
			$('input#id_weblink')
				.before("<span class='form-help-inline'>&nbsp;&nbsp;{% trans 'You cannot enter a weblink with more than 200 caracteres.' %}</span>")
				.parents('div.form-group').addClass('has-error');
		}
		if (document.getElementById('id_role').value == '') {
			$('select#id_role')
				.before("<span class='form-help-inline'>&nbsp;&nbsp;{% trans 'Please enter a role.' %}</span>")
				.parents('div.form-group').addClass('has-error');
		}
		var id = parseInt(document.getElementById('id_contributor').value);
		var new_role = document.getElementById('id_role').value;
		var new_name = document.getElementById('id_name').value;
		$('#table_list_contributors tbody > tr').each(function() {
			if (id != $(this).find('input[name=id]')[0].value && $(this).find('td[class=contributor_name]')[0].innerHTML == new_name && $(this).find('td[class=contributor_role]')[0].innerHTML == new_role) {
				var text = "{% trans 'There is already a contributor with this same name and role in the list.' %}.";
				msg += '<br/>' + text;
				return msg;
			}
		});
	} else if (form == 'form_track') {
		var element = document.getElementById('id_kind');
		var value = element.options[element.selectedIndex].value;
		var kind = element.options[element.selectedIndex].text;
		if (value != 'subtitles' && value != 'captions') {
			$('select#id_kind')
				.after("<span class='form-help-inline'>{% trans 'Please enter a correct kind.' %}</span>")
				.parents('div.form-group').addClass('has-error');
		}
		var element = document.getElementById('id_lang');
		var lang = element.options[element.selectedIndex].text;
		if (element.options[element.selectedIndex].value == '') {
			$('select#id_lang')
				.after("<span class='form-help-inline'>{% trans 'Please select a language.' %}</span>")
				.parents('div.form-group').addClass('has-error');
		}
		if (document.getElementById('id_src').value == '') {
			$('input#id_src')
				.after("<span class='form-help-inline'>{% trans 'Please specify a track file.' %}</span>")
				.parents('div.form-group').addClass('has-error');
		}
		if (document.getElementById('file-picker-path').innerHTML.split(' ')[1] != '(VTT)') {
			$('input#id_src')
				.after("<span class='form-help-inline'>{% trans 'Only .vtt format is allowed.' %}</span>")
				.parents('div.form-group').addClass('has-error');
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
				.after("<br><span class='form-help-inline'>{% trans 'There is already a track with the same kind and language in the list.' %}</span>")
				.parents('div.form-group').addClass('has-error');
		}
	} else if (form == 'form_document') {
		if ($('img#id_document_thumbnail_img').attr('src') == '/static/icons/nofile_48x48.png') {
			$('img#id_document_thubmanil_img')
				.before("<span class='form-help-inline'>&nbsp;&nbsp;{% trans 'Please select a document.' %}</span>")
				.parents('div.form-group').addClass('has-error');
		}
	} else if (form == 'form_overlay') {
		var tags = /<script.+?>|<iframe.+?>/;
		if (tags.exec(document.getElementById('id_content').value) != null) {
			$('textarea#id_content')
				.before("<span class='form-help-inline'>&nbsp;&nbsp;{% trans 'Iframe and Script tags are not allowed.' %}</span>")
				.parents('div.form-group').addClass('has-error');
		}
	}
	return msg;
}

$('.new-contributor').on('click')