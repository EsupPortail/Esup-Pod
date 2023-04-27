document.addEventListener('DOMContentLoaded', function () {
    const cards = document.getElementsByClassName("video-card");
    for (let card of cards) {
        const form = card.querySelector(".favorite-button-form-card");

        form.addEventListener('submit', function (e) {
            e.preventDefault();

            const formData = new FormData(form)

            fetch(form.action, {
                method: form.method,
                body: formData
            })
                .then(response => response.text()) // On récupère le contenu HTML de la réponse
                .then(data => {
                    const parser = new DOMParser();
                    const html = parser.parseFromString(data, 'text/html');
                    card.remove();
                })
                .catch(error => {
                    alert("La suppression n'a pas pu se faire...")
                });
        });
    }
});