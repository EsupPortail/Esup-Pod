/*
 * jQuery plugin for django-file-picker
 * Author: Caktus Consulting Group, LLC (http://www.caktusgroup.com/)
 * Source: https://github.com/caktus/django-file-picker
 *
 * Copyright (C) 2011 by Caktus Consulting Group, LLC
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */
"use strict";

(function ($) {

    // don't use square bracket syntax (jQuery 1.4.x)
    // source: http://benalman.com/news/2009/12/jquery-14-param-demystified/
    $.ajaxSetup({ traditional: true });

    $.filePicker = {
        conf: {
            url: '',
            urls: ''
        }
    };

    // constructor
    function FilePicker(root, conf) {   
        
        // current instance
        var self = this,
            tabs = null,
            browse_pane = null,
            upload_pane = null,
            dir_pane = null,
            current_dir = {};
        root.data('overlay').onLoad(function () {
            this.getOverlay().data('filePicker').load();
            $('.file-picker-overlay').css('z-index', '1');
            $('img').css('z-index', '0');
        });
        root.data('overlay').onClose(function () {
            upload_pane.empty();
            browse_pane.empty();
            dir_pane.empty();
            $('.plupload').remove();
        });
        root.append($('<div>').addClass('file-picker'));
        root = root.find('.file-picker');
        
        // methods
        $.extend(self, {

            getConf: function () {
                return conf;    
            },
            
            getRoot: function () {
                return root;    
            },

            load: function () {
                tabs.tabs('div.panes > div.pane');
                $(tabs).data('tabs').onClick(function (e, index) {
                    self.tabClick(e, index);
                });
                $.get(conf.url, function (response) {
                    conf.urls = response.urls;
                    self.current_dir = {};
                    self.current_dir.name = 'Home';
                    self.getDir();
                });
            },

            tabClick: function (e, index) {
                $('.plupload').remove();
                if (index === 2) {
                    self.getForm();
                } else if (index === 1) {
                    self.getFiles({'directory': self.current_dir.id});
                } else if (index === 0) {
                    self.getDir({'directory': self.current_dir.id});
                }
            },

            getDir: function(data) {
                if (!data) {
                    $.get(conf.urls.directories.file, {}, function (response) {
                        self.displayDir(response);
                        self.current_dir.id = response.result.id;
                        self.current_dir.name = response.result.parent;
                    });
                } else {
                    $.get(conf.urls.directories.file, data, function (response) {
                        self.displayDir(response);
                    });
                }
            },

            editDir: function(data) {
                if (!data) {
                    $.get(conf.urls.directories.configure, {action: 'new', id: self.current_dir.id}, function (response) {
                        self.displayConfigure(response, 'new');
                    });
                } else {
                    $.get(conf.urls.directories.configure, data, function (response) {
                        self.displayConfigure(response, data.action);
                    });
                }
            },

            saveDir: function(data) {
                if (!data) {
                    return 0;
                } else {
                    $.post(conf.urls.directories.configure, data, function (response) {
                        if (response.errors) {
                            $.each(response.errors, function(idx, category) {
                                $.each(category, function(idx, error) {
                                    $('#configure_form_errors').empty();
                                    var msg = $('<p>').text(error);
                                    $('#configure_form_errors').append(msg);
                                });
                            });
                            return;
                        } else {
                            self.getDir({directory: self.current_dir.id});
                        }
                    });
                }
            },

            displayConfigure: function(data, action) {
                var pane = root.find('.file-picker-directories');
                pane.empty();
                var form = $('<form>').attr({
                    'method': 'post',
                    'class': 'configure_form',
                });
                if (action == 'new') {
                    var table = $('<table>').html(data.form);
                    form.append(table);
                    var action = $('<input>').attr({
                        'type': 'hidden',
                        'name': 'action',
                        'value': 'new'
                    });
                    form.append(action);
                    var submit = $('<input>').attr({
                        'type': 'submit',
                        'value': 'Submit'
                    }).click(function (e) {
                        e.preventDefault();
                        var form = dir_pane.find('.configure_form');
                        data = {};
                        $(':input', form).each(function () {
                            data[this.name] = this.value;
                        });
                        self.saveDir(data);
                    });
                    form.append(submit);
                }
                if (action == 'edit') {
                    var table = $('<table>').html(data.form);
                    form.append(table);
                    var action = $('<input>').attr({
                        'type': 'hidden',
                        'name': 'action',
                        'value': 'edit',
                    });
                    form.append(action);
                    var id = $('<input>').attr({
                        'type': 'hidden',
                        'name': 'id',
                        'value': data.id
                    });
                    form.append(id);
                    var submit = $('<input>').attr({
                        'type': 'submit',
                        'value': 'Submit'
                    }).click(function (e) {
                        e.preventDefault();
                        var form = dir_pane.find('.configure_form');
                        data = {};
                        $(':input', form).each(function () {
                            data[this.name] = this.value;
                        });
                        self.saveDir(data);
                    });
                    form.append(submit);
                }
                if (action == 'delete') {
                    form.append($('<p>').text('Are you sure you want to delete this directory ?'));
                    var action = $('<input>').attr({
                        'type': 'hidden',
                        'name': 'action',
                        'value': 'delete',
                    });
                    form.append(action);
                    var id = $('<input>').attr({
                        'type': 'hidden',
                        'name': 'id',
                        'value': data.id
                    });
                    form.append(id);
                    var submit = $('<input>').attr({
                        'type': 'submit',
                        'value': 'Yes'
                    }).click(function (e) {
                        e.preventDefault();
                        var form = dir_pane.find('.configure_form');
                        data = {};
                        $(':input', form).each(function () {
                            data[this.name] = this.value;
                        });
                        self.saveDir(data);
                    });
                    form.append(submit);
                }
                var cancel = $('<a>').click(function (e) {
                    self.getDir({'directory': self.current_dir.id});
                });
                cancel.addClass('file-picker-back');
                cancel.append($('<img>').attr('src', '/static/img/back.png'));
                pane.append(cancel);
                pane.append(form);
                pane.append($('<div>').attr('id', 'configure_form_errors'));
            },

            displayDir: function(data) {
                var dirs = data.result;
                var current = Object.keys(dirs)[0];
                var pane = root.find('.file-picker-directories');
                pane.empty();
                var title = $('<h2>').text(dirs['path']);
                // Back Button
                if (current != 'Home') {
                    var back = $('<a>').click(function (e) {
                        self.getDir({'directory': dirs.id});
                        self.current_dir.id = dirs.id;
                        self.current_dir.name = dirs.parent;
                    });
                    back.addClass('file-picker-back');
                    back.append($('<img>').attr('src', '/static/img/back.png'));
                    pane.append(back);
                }
                // View Button
                var view = $('<a>').click(function (e) {
                    $('.file-picker-tabs li a')[2].click()
                });
                var img = $('<img>').attr('src', '/static/img/view.png');
                view.addClass('file-picker-directory view');
                view.append(img);
                pane.append(view);
                pane.append(title);
                // Sub Directories category
                pane.append($('<h3>').text('Sub-directories :'));
                // List of sub directories
                if (dirs[current].length > 0) {
                    var table = $('<table>').addClass('directories-list');
                    var newdir = null;
                    var newsize = null;
                    $.each(dirs[current], function(index, dir) {
                        if (index % 5 == 0) {
                            newdir = $('<tr>');
                            newsize = $('<tr>');
                            table.append(newdir);
                            table.append(newsize);
                        }
                        var a = $('<a>').click(function (e) {
                            self.getDir({'directory': dir.id});
                            self.current_dir.id = dir.id;
                            self.current_dir.name = dir.name;
                        });
                        if (dir.last && dir.size == 0) {
                            var img = $('<img>').attr('src', '/static/img/directory-closed.png');
                            a.addClass('file-picker-directory closed');
                        } else {
                            var img = $('<img>').attr('src', '/static/img/directory-opened.png');
                            a.addClass('file-picker-directory opened');
                        }
                        a.append(img).append(dir.name);
                        newdir.append($('<td>').append(a));

                        //

                        var td = $('<td>').text('Files: ' + dir.size);
                        var edit = $('<a>').click(function (e) {
                            self.editDir(
                                {'action': 'edit',
                                 'id': dir.id});
                        });
                        var img = $('<img>').attr('src', '/static/img/edit.png');
                        edit.addClass('file-picker-directory edit');
                        edit.append(img);
                        td.append(edit);

                        var del = $('<a>').click(function (e) {
                            self.editDir(
                                {'action': 'delete',
                                 'id': dir.id});
                        });
                        var img = $('<img>').attr('src', '/static/img/delete.png');
                        del.addClass('file-picker-directory delete');
                        del.append(img);
                        td.append(del);

                        newsize.append(td);
                    });
                    // Add directory button at end
                    var img = $('<img>').attr('src', '/static/img/add.png');
                    var add = $('<a>').click(function (e) {
                        self.editDir();
                    });
                    add.addClass('file-picker-directory add');
                    add.append(img);
                    newdir.append(add);
                    table.append(newdir);
                    table.append(newsize);
                    pane.append(table);
                } else {
                    // Add directory button at end
                    var img = $('<img>').attr('src', '/static/img/add.png');
                    var add = $('<a>').click(function (e) {
                        self.editDir();
                    });
                    add.addClass('file-picker-directory add');
                    add.append(img);
                    pane.append($('<p>').text('No sub-directories.').append(add));
                }
                // Current directory info category
                pane.append($('<hr>'));
                pane.append($('<h3>').text('Info'));
                pane.append($('<p>').text('You have ' + dirs['size'] + ' file(s) in this directory.'));
            },
            
            getForm: function (data) {
                if (!data) {
                    $.get(conf.urls.upload.file, {directory: self.current_dir.id}, function (response) {
                        self.displayForm(response);
                        self.setupUpload();
                    });
                } else {
                    $.post(conf.urls.upload.file, data, function (response) {
                        if (response.errors) {
                            $.each(response.errors, function (idx) {
                                console.error(this);
                            });
                            return;
                        }
                        if (response.insert) {
                            $(self).trigger("onImageClick", [response.insert]);
                            self.getForm();
                        } else {
                            self.displayForm(response);
                            self.setupUpload();
                            var upload_form = upload_pane.find('.upload_form');
                            var submit = $('<input>').attr({
                                'type': 'submit',
                                'value': 'Submit'
                            }).click(function (e) {
                                e.preventDefault();
                                var upload_form = upload_pane.find('.upload_form');
                                data = {};
                                $(':input', upload_form).each(function () {
                                    data[this.name] = this.value;
                                });
                                self.getForm(data);
                            });
                            upload_form.append(submit);
                        }
                    });
                }
            },
            
            displayForm: function (data) {
                var pane = root.find('.file-picker-upload');
                pane.empty();
                pane.append($('<h2>').text('Select file to upload / ' + self.current_dir.name));
                var browse = $('<input>').val('Select a file').attr({
                    'type': 'button',
                    'id': 'select-a-file'
                }).addClass('select-a-file');
                pane.append(browse);
                var runtime = $('<div>').addClass('runtime');
                pane.append(runtime);
                pane.append($('<ul>').addClass('upload-list'));
                pane.append($('<h3>').text('File details'));
                var form = $('<form>').attr({
                    'method': 'post',
                    'class': 'upload_form',
                    'action': ""
                });
                var table = $('<table>').html(data.form);
                form.append(table);
                pane.append(form);
            },
            
            getFiles: function (data) {
                if (!data) {
                    data = {};
                }
                $.get(conf.urls.browse.files, data, function (response) {
                    self.displayFiles(response);
                });
            },
            
            setupUpload: function () {
                var ajaxUpload = new AjaxUpload('select-a-file', {
                    action: conf.urls.upload.file,
                    autoSubmit: true,
                    responseType: 'json',
                    onSubmit: function(file, extension) {
                        $('.runtime').html(
                            'Uploading ...'
                        );
                        $('.add_to_model').remove();
                    },
                    onComplete: function(file, response) {
                        $('.runtime').html(
                            'Uploading ... Complete'
                        );
                        var submit = $('<input>').attr({
                            'class': 'add_to_model',
                            'type': 'submit',
                            'value': 'Submit'
                        }).click(function (e) {
                            e.preventDefault();
                            var upload_form = upload_pane.find('.upload_form');
                            var data = {};
                            $(':input', upload_form).each(function () {
                                data[this.name] = this.value;
                            });
                            data.file = response.name;
                            self.getForm(data);
                        });
                        var upload_form = upload_pane.find('.upload_form');
                        upload_form.append(submit);
                    }
                });
            },

            displayFiles: function (data) {
                var files = data.result;
                browse_pane.empty();
                browse_pane.append($('<h2>').text('Select file to insert / ' + self.current_dir.name));
                var table = $('<table>').addClass('file-list');
                var tr = $('<tr>');
                var form = $('<form>').attr({
                    'action': "",
                    'method': 'get',
                    'class': 'file-picker-search'
                });
                form.append(
                    $('<input>').attr({
                        'type': 'text',
                        'class': 'search_val',
                        'name': 'search'
                    }).val(data.search)
                );
                form.append(
                    $('<input>').attr({
                        'type': 'submit',
                        'value': 'Search'
                    }).addClass('search_val').click(function (e) {
                        e.preventDefault();
                        self.getFiles({
                            'search': browse_pane.find('.search_val').val(),
                            'directory': self.current_dir.id
                        });
                    })
                );
                if (files.length > 0) {
                    tr = $('<tr>');
                    $.each(data.link_headers, function (idx, value) {
                        tr.append($('<th>').text(value));
                    });
                    $.each(data.extra_headers, function (idx, value) {
                        tr.append($('<th>').text(value));
                    });
                }
                table.append(tr);
                $.each(files, function (idx, file) {
                    var tr = $('<tr>');            
                    $.each(file.link_content, function (idx, value) {
                        var a = $('<a>').click(function (e) {
                            $(self).trigger("onImageClick", file.extra);
                        });
                        a.append(value);
                        tr.append($('<td>').append(a));
                    });
                    $.each(data.columns, function (idx, key) {
                        tr.append($('<td>').append(file.extra[key]));
                    });
                    table.append(tr);
                });
                var div = $('<div>').attr({'class': 'scrollable'});
                browse_pane.append(form);
                browse_pane.append(div.append(table));
                var footer = $('<div>').attr('class', 'footer');
                var next = $('<a>').attr({
                    'title': 'Next',
                    'href': '#'
                }).text('Next');
                if (data.has_next) {
                    next.click(function (e) {
                        e.preventDefault();
                        self.getFiles({
                            'page': data.page + 1, 
                            'search': browse_pane.find('.search_val').val(),
                            'directory': self.current_dir.id
                        });
                    });
                } else {
                    next.css('color', '#bbb');
                }
                var previous = $('<a>').attr({
                    'title': 'Next',
                    'href': '#'
                }).text('Previous ');
                if (data.has_previous) {
                    previous.click(function (e) {
                        e.preventDefault();
                        self.getFiles({'page': data.page - 1, 
                        'search': browse_pane.find('.search_val').val()});
                    });
                } else {
                    previous.css('color', '#bbb');
                }
                footer.append(previous);
                $.each(data.pages, function (index, value) { 
                    var list = $('<a>').attr({
                        'title': value,
                        'href': '#'
                    }).text(value + ' ');
                    if (data.page === value) {
                        list.css('color', '#bbb');
                    } else {
                        list.click(function (e) {
                            e.preventDefault();
                            self.getFiles({
                                'page': value, 
                                'search': browse_pane.find('.search_val').val()
                            });
                        });
                    }
                    footer.append(list);
                });
                footer.append(next);
                browse_pane.append(footer);
            }
        });

        // callbacks    
        $.each(['onImageClick'], function (i, name) {
            // configuration
            if ($.isFunction(conf[name])) { 
                $(self).bind(name, conf[name]); 
            }
            self[name] = function (fn) {
                $(self).bind(name, fn);
                return self;
            };
        });
        
        // setup tabs
        tabs = $('<ul>').addClass('css-tabs').addClass('file-picker-tabs');
        tabs.append($('<li>').append($('<a>').attr('href', '#').text('Directories')));
        tabs.append($('<li>').append($('<a>').attr('href', '#').text('Browse')));
        tabs.append($('<li>').append($('<a>').attr('href', '#').text('Upload')));
        var panes = $('<div>').addClass('panes');
        dir_pane = $('<div>').addClass('file-picker-directories').addClass('pane');
        panes.append(dir_pane);
        browse_pane = $('<div>').addClass('file-picker-browse').addClass('pane');
        browse_pane.append($('<h2>').text('Browse for a file'));
        panes.append(browse_pane);
        upload_pane = $('<div>').addClass('file-picker-upload').attr({'id': 'file-picker-upload'}).addClass('pane');
        panes.append(upload_pane);
        root.append(tabs);
        root.append(panes);
    } 


    // jQuery plugin implementation
    $.fn.filePicker = function (conf) {
        // already constructed --> return API
        var el = this.data("filePicker");
        if (el) {
            return el;
        }

        conf = $.extend({}, $.filePicker.conf, conf);
        
        this.each(function () {
            el = new FilePicker($(this), conf);
            $(this).data("filePicker", el);
        });

        return conf.api ? el: this;
    };

})(jQuery);


function get_file_picker_types(el) {
    var picker_names = {};
    $.each($(el).attr('class').split(' '), function(idx, class_name) {
        if (class_name.substr(0, 17) == 'file_picker_name_') {
            var type = class_name.split('_')[3];
            var name = class_name.split('_')[4];
            picker_names[type] = name;
        }
    });
    return picker_names;
}

/*
function insertAtCaret(areaId,text) {
    console.log(areaId);
    console.log(text); 
    var txtarea = document.getElementById(areaId);
    var scrollPos = txtarea.scrollTop;
    var strPos = 0;
    var br = ((txtarea.selectionStart || txtarea.selectionStart == '0') ? "ff" : (document.selection ? "ie" : false ) );
    if (br == "ie") { txtarea.focus();
        var range = document.selection.createRange();
        range.moveStart ('character', -txtarea.value.length);
        strPos = range.text.length;
    } else if (br == "ff") strPos = txtarea.selectionStart;
    var front = (txtarea.value).substring(0,strPos);
    var back = (txtarea.value).substring(strPos,txtarea.value.length);
    txtarea.value=front+text+back;
    strPos = strPos + text.length;
    if (br == "ie") { 
        txtarea.focus();
        var range = document.selection.createRange();
        range.moveStart ('character', -txtarea.value.length);
        range.moveStart ('character', strPos);
        range.moveEnd ('character', 0);
        range.select();
    } else if (br == "ff") { 
        txtarea.selectionStart = strPos;
        txtarea.selectionEnd = strPos;
        txtarea.focus();
    }
    txtarea.scrollTop = scrollPos;
}
*/

function insertAtCaret(areaId, text) {
    var txtarea = $('#'+areaId);
    txtarea.attr('value', text.id);
    $('#file-picker-path').text(text.name + ' (' + text.file_type + ') ');
}