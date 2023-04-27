document.addEventListener('DOMContentLoaded', function () {
    const forms = document.getElementsByClassName("favorite-button-form-card");
    console.log(forms)
    for (let form of forms) {
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
                    form.remove();
                })
                .catch(error => {
                    alert("La suppression n'a pas pu se faire...")
                });
        });
    }
});