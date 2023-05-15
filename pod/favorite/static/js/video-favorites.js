document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById("favorite-button-form");
    form.addEventListener('submit', function (e) {
        e.preventDefault();
        const formData = new FormData(form)
        fetch(form.action, {
            method: form.method,
            body: formData
        })
            .then(response => response.text()) // We take the HTML content of the response
            .then(data => {
                const parser = new DOMParser();
                const html = parser.parseFromString(data, 'text/html');
                const updatedButton = html.querySelector("#star_btn");
                const button = document.querySelector("#star_btn");
                button.replaceWith(updatedButton);
            })
            .catch(error => {
                alert(gettext("The addition couldn't be completed..."));
            });
    });
});