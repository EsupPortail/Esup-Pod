let addQuestionButton = document.getElementById("add-question");
const totalNewForms = document.getElementById("id_questions-TOTAL_FORMS");

let defaultQuestionForms = document.querySelectorAll(".question-form");
for (defaultQuestionForm of defaultQuestionForms) {
  handleQuestionType(defaultQuestionForm);
}

let questionsTypeElements = document.querySelectorAll(".question-select-type");
for (questionTypeEl of questionsTypeElements) {
  addEventListenerQuestionType(questionTypeEl);
}

function addEventListenerQuestionType(questionTypeElement) {
  questionTypeElement.addEventListener("change", function (event) {
    console.log(event.target.value);
    let questionForm = questionTypeElement.closest(".question-form");
    handleQuestionType(questionForm);
  });
}

addQuestionButton.addEventListener("click", addNewQuestionForm);
let removeQuestionButtons = document.querySelectorAll(
  ".delete-question-button",
);
for (removeQuestionButton of removeQuestionButtons) {
  removeQuestionButton.addEventListener("click", removeQuestionForm);
}

function addNewQuestionForm(event) {
  if (event) {
    event.preventDefault();
  }

  const currentQuestionForms = document.getElementsByClassName("question-form");
  let currentFormCount = currentQuestionForms.length - 1;

  const formCopyTarget = document.getElementById("question-form-list");
  let copyEmptyQuestionFormEl = document
    .getElementById("empty-form")
    .cloneNode(true).firstElementChild;
  copyEmptyQuestionFormEl.setAttribute("class", "question-form");
  copyEmptyQuestionFormEl.removeAttribute("id");

  const regex = new RegExp("__prefix__", "g");
  copyEmptyQuestionFormEl.innerHTML = copyEmptyQuestionFormEl.innerHTML.replace(
    regex,
    currentFormCount,
  );
  totalNewForms.setAttribute("value", currentFormCount + 1);
  let newQuestionTypeElement = copyEmptyQuestionFormEl.querySelector(
    ".question-select-type",
  );
  addEventListenerQuestionType(newQuestionTypeElement);
  let removeQuestionButton = copyEmptyQuestionFormEl.querySelector(
    ".delete-question-button",
  );
  removeQuestionButton.addEventListener("click", removeQuestionForm);

  formCopyTarget.append(copyEmptyQuestionFormEl);
}

function removeQuestionForm(event) {
  if (event) {
    event.preventDefault();
  }

  const questionFormToDelete = event.target.closest(".question-form");
  questionFormToDelete.remove();
  const currentQuestionForms = document.getElementsByClassName("question-form");
  totalNewForms.setAttribute("value", currentQuestionForms.length - 1);
}

function handleShortAnswerQuestion(questionForm) {
  const input = document.createElement("input");
  input.type = "text";
  input.name = questionForm.querySelector(".question-choices-form").name;
  input.placeholder = "The short answer";
  input.classList.add("short-answer-field");
  questionForm.querySelector(".question-choices-form").appendChild(input);
}

function handleLongAnswerQuestion(questionForm) {
  const textarea = document.createElement("textarea");
  textarea.name = questionForm.querySelector(".question-choices-form").name;
  textarea.placeholder = "The long answer";
  textarea.classList.add("long-answer-field");
  questionForm.querySelector(".question-choices-form").appendChild(textarea);
}

function handleUniqueChoiceQuestion(questionForm) {
  let choicesForm = questionForm.querySelector(".question-choices-form");

  let counter =
    document.querySelectorAll('.question-choices-form input[type="radio"]')
      .length + 1;

  const fieldset = document.createElement("fieldset");
  const legend = document.createElement("legend");
  legend.textContent = "Vos choix";
  fieldset.appendChild(legend);

  for (let i = 0; i < 2; i++) {
    const choiceDiv = document.createElement("div");
    choiceDiv.classList.add("form-check");

    const input = document.createElement("input");
    input.type = "radio";
    input.classList.add("form-check-input");
    input.name = `choices_${counter}`;

    const textInput = document.createElement("input");
    textInput.type = "text";
    textInput.placeholder = `Choice ${i + 1}`;

    choiceDiv.appendChild(input);
    choiceDiv.appendChild(textInput);

    fieldset.appendChild(choiceDiv);
  }

  choicesForm.appendChild(fieldset);

  const addButton = document.createElement("button");
  addButton.textContent = "Add a choice";
  addButton.type = "button";
  addButton.classList.add("btn", "btn-outline-secondary", "btn-sm", "mt-2");
  addButton.addEventListener("click", function () {
    const newChoiceDiv = document.createElement("div");
    newChoiceDiv.classList.add("form-check");

    const input = document.createElement("input");
    input.type = "radio";
    input.classList.add("form-check-input");
    input.name = `choices_${counter}`;

    const textInput = document.createElement("input");
    textInput.type = "text";
    textInput.placeholder = `Choice ${choicesForm.querySelectorAll('.question-choices-form input[type="radio"]').length + 1}`;

    newChoiceDiv.appendChild(input);
    newChoiceDiv.appendChild(textInput);

    fieldset.appendChild(newChoiceDiv);
  });

  choicesForm.appendChild(addButton);
}

function handleQuestionType(questionForm) {
  const questionType = questionForm.querySelector(
    ".question-select-type",
  ).value;

  let questionChoicesForm = questionForm.querySelector(
    ".question-choices-form",
  );
  if (!questionChoicesForm) {
    let choicesSection = questionForm.querySelector(
      ".question-choices-section",
    );
    let newChoicesForm = document.createElement("form");
    newChoicesForm.setAttribute("action", "post");
    newChoicesForm.classList.add("question-choices-form");

    choicesSection.appendChild(newChoicesForm);
  }
  questionForm.querySelector(".question-choices-form").innerHTML = "";

  if (questionType === "short_answer") {
    handleShortAnswerQuestion(questionForm);
  } else if (questionType === "long_answer") {
    handleLongAnswerQuestion(questionForm);
  } else if (questionType === "unique_choice") {
    handleUniqueChoiceQuestion(questionForm);
  } // Add other conditions for other question types.
}

function manage_form_submission() {
  let submissionButton = document.getElementById("quiz-submission-button");

  submissionButton.addEventListener("click", (event) => {
    if (event) {
      event.preventDefault();
    }

    let questionFormsList = document.querySelectorAll(".question-form");
    for (questionForm of questionFormsList) {
      const questionType = questionForm.querySelector(
        ".question-select-type",
      ).value;
      if (questionType === "short_answer") {
        let shortAnswerInput = questionForm.querySelector(
          ".short-answer-field",
        );
        let hiddenShortAnswerInput = questionForm.querySelector(
          ".hidden-short-answer-field",
        );
        hiddenShortAnswerInput.value = shortAnswerInput.value;
      } else if (questionType === "long_answer") {
        let longAnswerInput = questionForm.querySelector(".long-answer-field");
        let hiddenLongAnswerInput = questionForm.querySelector(
          ".hidden-long-answer-field",
        );
        hiddenLongAnswerInput.value = longAnswerInput.value;
      } else if (questionType === "unique_choice") {
        let choicesData = {};

        const radioInputs = questionForm.querySelectorAll(
          '.form-check > input[type="radio"]',
        );
        const textInputs = questionForm.querySelectorAll(
          '.form-check > input[type="text"]',
        );
        console.log(radioInputs);
        console.log(textInputs);
        radioInputs.forEach((input, index) => {
          choicesData[textInputs[index].value] = input.checked;
        });

        let hiddenUniqueChoiceAnswerInput = questionForm.querySelector(
          ".hidden-unique-choice-field",
        );
        hiddenUniqueChoiceAnswerInput.value = JSON.stringify(choicesData);
      } // Add other conditions for other question types.
    }

    let form = document.getElementById("quiz-form");
    form.submit();
  });
}

manage_form_submission();
