from django import forms


class BaseFilePickerWidget(forms.TextInput):
    """
    FilePicker base widget. Can be add on a CustomFileModel or 
    CustomImageModel foreignkey field.
    """

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
    """
    FilePicker custom widget. It's the widget you can use and personnalize.
    All JavaScripts and Stylesheets needed for FilePicker are added here. 
    """

    def __init__(self, pickers, *args, **kwargs):
        kwargs['classes'] = ['simple-filepicker']
        super(CustomFilePickerWidget, self).__init__(pickers, *args, **kwargs)

    class Media:
        css = {
            'all': ('css/filepicker.overlay.css',),
        }
        js = ('js/jquery.overlay.js',
              'js/ajaxupload.js',
              'js/jquery.filepicker.js',
              'js/filepicker.custom.js',)
