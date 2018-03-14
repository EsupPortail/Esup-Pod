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