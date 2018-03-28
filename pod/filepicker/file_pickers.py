from pod.filepicker.views import FilePickerBase
from pod.filepicker.views import ImagePickerBase
from pod.filepicker.forms import CustomFileForm
from pod.filepicker.forms import CustomImageForm


class CustomFilePicker(FilePickerBase):
    form = CustomFileForm
    columns = ('name', 'file_type', 'date_modified')
    extra_headers = ('Name', 'File type', 'Date modified', 'Delete')


class CustomImagePicker(ImagePickerBase):
    form = CustomImageForm
    link_headers = ['Thumbnail', ]

filepicker.site.register(CustomFileModel, CustomFilePicker, name='file')
filepicker.site.register(CustomImageModel, CustomImagePicker, name='img')