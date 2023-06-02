document.addEventListener("DOMContentLoaded", function () {
  const playlists = document.getElementById("playlist-list").children;
  const buttons = [];
  for (let playlist of playlists) {
    buttons.push(playlist.querySelector(".action-btn"));
  }

  for (let button of buttons) {
    preventRefreshButton(button);
  }
});

function preventRefreshButton(button) {
  if (button) {
    button.addEventListener("click", function (e) {
      e.preventDefault();
      const url = this.getAttribute("href");
      fetch(url, {
        method: "GET"
      })
        .then((response) => {
          if (response.ok) {
            return response.text();
          } else {
            throw new Error("Network response was not ok.");
          }
        })
        .then((data) => {
          const parser = new DOMParser();
          const html = parser.parseFromString(data, "text/html");
          const updatedButton = html.getElementById(button.id);
          preventRefreshButton(updatedButton)
          button.replaceWith(updatedButton);
        })
        .catch(error => {
          console.error("Error : ", error)
        });
    });
  }
}
