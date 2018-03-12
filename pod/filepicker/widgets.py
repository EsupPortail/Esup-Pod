from django import forms


class BaseFilePickerWidget(forms.URLInput):

    def __init__(self, pickers, *args, **kwargs):
        self.pickers = pickers
        classes = kwargs.pop('classes', ['filepicker'])
        super(BaseFilePickerWidget, self).__init__(*args, **kwargs)
        if 'file' in pickers:
            classes.append('file_picker_name_file_%s' % pickers['file'])
        if 'image' in pickers:
            classes.append('file_picker_name_image_%s' % pickers['image'])
        self.attrs['class'] = ' '.join(classes)


class CustomFilePickerWidget(BaseFilePickerWidget):

    def __init__(self, pickers, *args, **kwargs):
        kwargs['classes'] = ['simple-filepicker']
        super(CustomFilePickerWidget, self).__init__(pickers, *args, **kwargs)

    class Media:
        css = {'all': ('css/filepicker.overlay.css',)}
        js = ('js/ajaxupload.js',
              'js/jquery.filepicker.js',
              'js/filepicker.custom.js',)
