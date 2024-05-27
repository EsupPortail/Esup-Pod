const questionList = document.querySelectorAll(".question-container");

for (questionElement of questionList) {
  let showResponseButton = questionElement.querySelector(
    ".show-response-button",
  );
  showResponseButton.addEventListener("click", function (event) {
    event.preventDefault();
    player.currentTime(this.attributes.start.value);
  });
}
