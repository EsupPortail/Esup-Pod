document.addEventListener('DOMContentLoaded', function () {
    const forms = document.getElementsByClassName("favorite-button-form-card");
    for (let form of forms) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            const formData = new FormData(form)
            fetch(form.action, {
                method: form.method,
                body: formData
            })
                .then(response => {
                    response.text(); // We take the HTML content of the response
                    form.remove();
                })
                .catch(error => {
                    alert(gettext('The deletion couldn\'t be completed...'));
                });
        });
    }
});
