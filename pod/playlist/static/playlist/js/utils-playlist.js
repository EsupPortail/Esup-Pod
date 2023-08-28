/**
 * Disables the default refresh behavior of a button and performs an asynchronous GET request using the Fetch API.
 * @param {HTMLElement} button - The HTML button element.
 */
function preventRefreshButton(button, jsonFormat) {
  const FAVORITE_BUTTON_ID = 'favorite-button';
  const PLAYLIST_MODAL_ID = 'playlist-list';
  if (button) {
    button.addEventListener('click', function (e) {
      e.preventDefault();
      console.log("oui")
      let url = this.getAttribute('href');
      if (button.classList.contains('action-btn')) {
        button.classList.add('disabled');
        button.style.backgroundColor = 'gray';
        this.removeAttribute('href');
      } else if (button.classList.contains('favorite-btn-link')) {
        button.classList.add('disabled');
      }
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
            const favoriteButton = document.getElementById(FAVORITE_BUTTON_ID);
            const playlistModal = document.getElementById(PLAYLIST_MODAL_ID);
            preventRefreshButton(updatedButton);
            button.replaceWith(updatedButton);
            if (playlistModal && button.id === FAVORITE_BUTTON_ID) {
              playlistModal.replaceWith(html.getElementById(PLAYLIST_MODAL_ID));
              addEventListenerForModal();
            }
            if (favoriteButton && button.id !== FAVORITE_BUTTON_ID) {
              const updatedFavoriteButton = html.getElementById(FAVORITE_BUTTON_ID);
              preventRefreshButton(updatedFavoriteButton, false);
              favoriteButton.replaceWith(updatedFavoriteButton);
            }
          }
        })
        .catch(error => {
          console.error('Error : ', error);
        });
    });
  }
}
