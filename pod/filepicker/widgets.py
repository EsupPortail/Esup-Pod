from file_picker.widgets import FilePickerWidget


class CustomFilePickerWidget(FilePickerWidget):

    def __init__(self, pickers, *args, **kwargs):
        kwargs['classes'] = ['simple-filepicker']
        super(CustomFilePickerWidget, self).__init__(pickers, *args, **kwargs)

    class Media:
        css = {'all': ('css/filepicker.overlay.css',)}
        js = ('js/ajaxupload.js',
              'js/jquery.filepicker.js',
              'js/jquery.filepicker.simple.js',
              'js/filepicker.custom.js')
