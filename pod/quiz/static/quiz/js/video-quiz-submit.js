const questionList = document.querySelectorAll(".question-container");

for (questionElement of questionList) {
  let showResponseButton = questionElement.querySelector(
    ".show-response-button",
  );
  if(showResponseButton) {
    showResponseButton.addEventListener("click", function (event) {
      event.preventDefault();
      if(player.paused()) {
        player.play()
      }
      player.currentTime(this.attributes.start.value);
    });
  }
  
  // get all answer and parse it
  // if answer in good answer, put it in green else if user answer put it in red
  let questionid = questionElement.dataset.questionid;
  let allanswers = questionElement.querySelectorAll(`ul#id_${questionid}-selected_choice li input`);
  for (answer of allanswers) {
    if (questions_answers[`${questionid}`]) {
      let user_answer = questions_answers[`${questionid}`][0];
      let correct_answer = questions_answers[`${questionid}`][1];
      if( (Array.isArray(correct_answer) && correct_answer.includes(answer.value)) || correct_answer === answer.value ){
        answer.closest('li').classList.add('alert', 'alert-success');
      } else if ((Array.isArray(user_answer) && user_answer.includes(answer.value)) || user_answer === answer.value ){
        answer.closest('li').classList.add('alert', 'alert-danger');
      }
      if ((Array.isArray(user_answer) && user_answer.includes(answer.value)) || user_answer === answer.value ){
        answer.checked = true;
      }
    }
  } 
}
