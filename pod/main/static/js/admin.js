const selected = document.getElementById("id_data_type");
fieldChannel = document.getElementsByClassName('field-Channel');
fieldTheme = document.getElementsByClassName('field-Theme');
fieldPlaylist = document.getElementsByClassName('field-Playlist');
fieldChannel[0].style.display = 'none';
fieldTheme[0].style.display = 'none';
fieldPlaylist[0].style.display = 'none';

if (selected) {
 selected.addEventListener('change', function() {
    if (selected.value == 'channel') {
        fieldChannel[0].style.display = 'block';
        fieldTheme[0].style.display = 'none';
        fieldPlaylist[0].style.display = 'none';
    }
    else if (selected.value == 'theme') {
        fieldTheme[0].style.display = 'block';
        fieldChannel[0].style.display = 'none';
        fieldPlaylist[0].style.display = 'none';
    }
    else if (selected.value == 'playlist') {
        fieldPlaylist[0].style.display = 'block';
        fieldTheme[0].style.display = 'none';
        fieldChannel[0].style.display = 'none';
    }
    else {
        fieldChannel[0].style.display = 'none';
        fieldTheme[0].style.display = 'none';
        fieldPlaylist[0].style.display = 'none';
    }
});  
}