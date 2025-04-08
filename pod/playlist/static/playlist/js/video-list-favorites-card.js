document.addEventListener("DOMContentLoaded", function () {
  const favoritesButtons = document.getElementsByClassName("favorite-btn-link");
  for (let btn of favoritesButtons) {
    preventRefreshButton(btn, false);
  }
});
