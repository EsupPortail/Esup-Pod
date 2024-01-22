(function($){
    $(document).ready(function(){
        function toggleEventField() {
            var dataTypeField = $('#id_data_type');
            var eventField = $('#id_Event');

            if (dataTypeField.val() === 'event') {
                eventField.show();
            } else {
                eventField.hide();
            }
        }

        // Attachez la fonction à l'événement change du champ data_type
        $('#id_data_type').change(toggleEventField);

        // Appelez la fonction lors du chargement initial du formulaire
        toggleEventField();
    });
})(django.jQuery);
