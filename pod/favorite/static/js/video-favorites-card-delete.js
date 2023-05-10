document.addEventListener('DOMContentLoaded', function () {
    const cards = document.getElementsByClassName("draggable-container");
    const title = document.getElementById("video_count")
    for (let card of cards) {
        const form = card.querySelector(".favorite-button-form-card");
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            const formData = new FormData(form);
            fetch(form.action, {
                method: form.method,
                body: formData
            })
                .then(response => response.text()) // We take the HTML content of the response
                .then(data => {
                    const parser = new DOMParser();
                    const html = parser.parseFromString(data, 'text/html');
                    card.remove();
                    title.textContent = html.getElementById("video_count").textContent;
                    document.title = html.title;
                })
                .catch(error => {
                    alert("La suppression n'a pas pu se faire...");
                });
        });
    }
});