/**
 * Disables the default refresh behavior of a button and performs an asynchronous GET request using the Fetch API.
 * @param {HTMLElement} button - The HTML button element.
 */
function preventRefreshButton(button, jsonFormat) {
  if (button) {
    button.addEventListener('click', function (e) {
      e.preventDefault();
      let url = this.getAttribute('href');
      if (jsonFormat) {
        url += '?json=true'
      }
      fetch(url, {
        method: "GET"
      })
        .then((response) => {
          if (response.ok) {
            if (jsonFormat) {
              return response.json();
            }
            return response.text();
          } else {
            throw new Error('Network response was not ok.');
          }
        })
        .then((data) => {
          if (jsonFormat) {
            const starIconElement = button.querySelector('.bi');
            if (data.state === 'in-playlist') {
              const newUrl = url.replace('/add/', '/remove/');
              starIconElement.classList.remove('bi-star');
              starIconElement.classList.add('bi-star-fill');
              button.setAttribute('href', newUrl);
            } else if (data.state === 'out-playlist') {
              const newUrl = url.replace('/remove/', '/add/');
              starIconElement.classList.remove('bi-star-fill');
              starIconElement.classList.add('bi-star');
              button.setAttribute('href', newUrl);
            }
            preventRefreshButton(button, jsonFormat);
          } else {
            const parser = new DOMParser();
            const html = parser.parseFromString(data, 'text/html');
            const updatedButton = html.getElementById(button.id);
            preventRefreshButton(updatedButton);
            button.replaceWith(updatedButton);
          }
        })
        .catch(error => {
          console.error('Error : ', error);
        });
    });
  }
}
