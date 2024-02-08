const selectedType = document.getElementById("id_type");
const selectedDataType = document.getElementById("id_data_type");
fieldDataType = document.getElementsByClassName('field-data_type');
fieldChannel = document.getElementsByClassName('field-Channel');
fieldTheme = document.getElementsByClassName('field-Theme');
fieldPlaylist = document.getElementsByClassName('field-Playlist');
fieldHtml = document.getElementsByClassName('field-html');

if (selectedDataType.value != 'channel') {
    fieldChannel[0].style.display = 'none';
}

if (selectedDataType.value != 'theme') {
    fieldTheme[0].style.display = 'none';
}

if (selectedDataType.value != 'playlist') {
    fieldPlaylist[0].style.display = 'none';
}

if (selectedType.value != 'html') {
    fieldHtml[0].style.display = 'none';
}

if (selectedType) {
    selectedType.addEventListener('change', function() {
        if (selectedType.value == 'html') {
            fieldHtml[0].style.display = 'block';
            fieldDataType[0].style.display = 'none';
        } else {
            fieldHtml[0].style.display = 'none';
            fieldDataType[0].style.display = 'block';
        }
    });
}

if (selectedDataType) {
    selectedDataType.addEventListener('change', function() {
        if (selectedDataType.value == 'channel') {
            fieldChannel[0].style.display = 'block';
            fieldTheme[0].style.display = 'none';
            fieldPlaylist[0].style.display = 'none';
        } else if (selectedDataType.value == 'theme') {
            fieldTheme[0].style.display = 'block';
            fieldChannel[0].style.display = 'none';
            fieldPlaylist[0].style.display = 'none';
        } else if (selectedDataType.value == 'playlist') {
            fieldPlaylist[0].style.display = 'block';
            fieldTheme[0].style.display = 'none';
            fieldChannel[0].style.display = 'none';
        } else {
            fieldChannel[0].style.display = 'none';
            fieldTheme[0].style.display = 'none';
            fieldPlaylist[0].style.display = 'none';
        }
    });
}