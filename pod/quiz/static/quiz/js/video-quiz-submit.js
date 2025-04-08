/**
 * @file Esup-Pod video QUiz submission script.
 * @since 3.7.0
 */

// Read-only globals defined in video-script.html
/*
global player
*/
// Read-only globals defined in video_quiz.html
/*
global questions_answers, show_correct_answers
*/

const questionList = document.querySelectorAll(".question-container");

for (let questionElement of questionList) {
  let showResponseButton = questionElement.querySelector(
    ".show-response-button",
  );
  if (showResponseButton) {
    showResponseButton.addEventListener("click", function (event) {
      event.preventDefault();
      if (player.paused()) {
        player.play();
      }
      player.currentTime(this.attributes.start.value);
    });
  }

  let questionid = questionElement.dataset.questionid;

  // get all checkbox & radio answers and parse them.
  // if answer in good answer, put it in green else if user answer put it in red
  let allanswers = questionElement.querySelectorAll(`ul#id_${questionid}-selected_choice li input`);
  for (let answer of allanswers) {
    answer.disabled = true;
    if (questions_answers[`${questionid}`]) {
      let user_answer = questions_answers[`${questionid}`][0];
      // check if question is "single_choice", "multiple_choice", "short_answer"
      if ((Array.isArray(user_answer) && user_answer.includes(answer.value)) || user_answer === answer.value) {
        answer.checked = true;
      }
      if (show_correct_answers) {
        let correct_answer = questions_answers[`${questionid}`][1];
        if ((Array.isArray(correct_answer) && correct_answer.includes(answer.value)) || correct_answer === answer.value) {
          answer.closest('li').classList.add('bi', 'bi-clipboard-check', 'text-success');
          answer.closest('li').title = gettext("Correct answer given");
        } else if ((Array.isArray(user_answer) && user_answer.includes(answer.value)) || user_answer === answer.value) {
          answer.closest('li').classList.add('bi', 'bi-clipboard-x', 'text-danger');
          answer.closest('li').title = gettext("Incorrect answer given");
        } else {
          answer.closest('li').classList.add('bi', 'bi-clipboard');
        }
      }
    }
  }

  // case user input
  // Get short answer input
  let user_input = document.getElementById(`id_${questionid}-user_answer`);
  if (user_input) {
    user_input.disabled = true;
  }

  allanswersarr = Array.from(allanswers)
  if (user_input && !allanswersarr.includes(user_input) && questions_answers[`${questionid}`]) {
    let user_answer = questions_answers[`${questionid}`][0];
    if (user_input.tagName === 'INPUT') {
      user_input.value = user_answer;
    }
  }
}
