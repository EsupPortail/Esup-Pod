$(document).on('click', '.delete', function() {
	var url = $(this).parent().attr('action');
	var data = {
		'csrfmiddlewaretoken': $(this).parent().find('input').attr('value')
	}
	$.ajax({
		url: url,
		type: 'post',
		data: data,
		success: function(){
			alert('File successfully deleted.');
			$('.search_val').click();
		},
		fail: function(){
			alert('Error ! Cannot delete the file.');
		}
	});
});

jQuery(document).ready(function($) {

	var FILE_PICKER_ROOT = '/file-picker/';

	function install_file_picker(el, picker_names, urls) {
		var pickers = {};
        $.each(picker_names, function(type, name) {
            pickers[type] = urls[name];
        });
        var overlay = $('<div>').addClass('file-picker-overlay').overlay().filePicker({
            onImageClick: function(e, insert) {
                insertAtCaret(el.id, insert);
            }
        }).insertBefore($(el));
        var parent = $(el).parent();
        if (pickers.image) {
            var anchor = $('<a>').text('Insert Image').attr({
                'name': 'filepicker-image',
                'title': 'Insert Image',
                'href': '#'
            }).css('display', 'block').click(function(e) {
                e.preventDefault();
                var conf = $(overlay).data('filePicker').getConf();
                conf.url = pickers.image;
                $('input.simple-filepicker').attr('value', '');
                $(overlay).data('overlay').load();
            }).prependTo(parent);
        }
        if (pickers.file) {
            var anchor = $('<a>').text('Insert File').attr({
                'name': 'filepicker-file',
                'title': 'Insert File',
                'href': '#'
            }).css('display', 'block').click(function(e) {
                e.preventDefault();
                var conf = $(overlay).data('filePicker').getConf();
                conf.url = pickers.file;
                $('input.simple-filepicker').attr('value', '');
                $(overlay).data('overlay').load();
            }).prependTo(parent);
		}
	}

	$('input.simple-filepicker').each(function(idx, el) {
		var picker_names = get_file_picker_types(el);
		if (picker_names) {
			var names = [];
			$.each(picker_names, function(key, val) { names.push(val); });
			$.getJSON(FILE_PICKER_ROOT, {'pickers': names}, function(response) {
				install_file_picker(el, picker_names, response.pickers);
			});
		}
	});

    var baseInsertAtCaret = insertAtCaret;
    insertAtCaret = function(areaId, text) {
        $('input.simple-filepicker').attr('value', '');
        baseInsertAtCaret(areaId, text);
        $('input.simple-filepicker').attr('value', text);
    }
});