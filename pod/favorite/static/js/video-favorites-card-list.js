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
                    const button = form.querySelector("#star_btn > i");
                    button.classList.toggle("bi-star-fill");
                    button.classList.toggle("bi-star");
                })
                .catch(error => {
                    alert(gettext('The deletion couldn\'t be completed...'));
                });
        });
    }
});
