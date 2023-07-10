document.addEventListener("DOMContentLoaded", function () {
  const cards = document.getElementsByClassName("draggable-container");
  for (let card of cards) {
    const btn = card.querySelector(".remove-from-playlist-btn-link");
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      const url = btn.getAttribute("href");
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
          card.remove();
          const parser = new DOMParser();
          const html = parser.parseFromString(data, "text/html");
          const title = document.getElementById("video_count");
          title.replaceWith(html.getElementById("video_count"));
        })
        .catch(error => {
          console.error("Error : ", error)
        });
    })
  }
});
