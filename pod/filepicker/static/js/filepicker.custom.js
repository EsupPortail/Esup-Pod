$(document).on('click', '.delete-file', function() {
    var url = $(this).parent().attr('action');
    var data = {
        'csrfmiddlewaretoken': $(this).parent().find('input').attr('value')
    }
    if (confirm('Are you sure ?')) {
        $.ajax({
            url: url,
            type: 'post',
            data: data,
            success: function(){
                alert(gettext('File successfully deleted.'));
                $('.search_val').click();
            },
            fail: function(){
                alert(gettext('Error ! Cannot delete the file.'));
            }
        });
    }
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
            var conf = $(overlay).data('filePicker').getConf();
            conf.url = pickers.image;
            var anchor = $('<a>').text(gettext('Insert Image')).attr({
                'name': 'filepicker-image',
                'title': gettext('Insert Image'),
                'href': '#'
            }).css('display', 'block').click(function(e) {
                e.preventDefault();
                $(el).attr('value', '');
                $(el).next().text(gettext('Select a file...'));
                $(overlay).data('overlay').load();
            }).prependTo(parent);
        }
        if (pickers.file) {
            var conf = $(overlay).data('filePicker').getConf();
            conf.url = pickers.file;
            var anchor = $('<a>').text(gettext('Insert File')).attr({
                'name': 'filepicker-file',
                'title': gettext('Insert File'),
                'href': '#'
            }).css('display', 'block').click(function(e) {
                e.preventDefault();
                $(el).attr('value', '');
                $(el).next().text(gettext('Select a file...'));
                $(overlay).data('overlay').load();
            }).prependTo(parent);
		}
        var file_path = $('<p>').attr('id', 'file-picker-path');
        file_path.text(gettext('Select a file...'));
        if ($(el).attr('value') != '') {
            $.get(conf.url, function (response) {
                conf.urls = response.urls;
            }).done(function() {
                $.get(conf.urls.browse.file, {id: el.value}, function (response) {
                    file_path.text(response.result.name);
                    var thumb = $('<img>');
                    thumb.attr('id', 'file-picker-thumbnail');
                    thumb.attr('src', response.result.thumbnail);
                    thumb.attr('alt', gettext('Thumbnail'));
                    thumb.attr('width', 50);
                    thumb.attr('height', 50);
                    thumb.appendTo(file_path);
                });
            });
        }
        file_path.appendTo(parent);
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
        $(this).hide();
	});

    var baseInsertAtCaret = insertAtCaret;
    insertAtCaret = function(areaId, text) {
        $('#'+areaId).attr('value', '');
        return baseInsertAtCaret(areaId, text);
    }
});