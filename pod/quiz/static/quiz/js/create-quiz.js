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
  const currentFormCount = currentQuestionForms.length - 1;

  const formCopyTarget = document.getElementById("question-form-list");
  const copyEmptyQuestionFormEl = cloneQuestionForm(currentFormCount);

  const newQuestionTypeElement = copyEmptyQuestionFormEl.querySelector(".question-select-type");

  handleQuestionForm(copyEmptyQuestionFormEl);
  addEventListenerQuestionType(newQuestionTypeElement);

  const removeQuestionButton = copyEmptyQuestionFormEl.querySelector(".delete-question-button");
  removeQuestionButton.addEventListener("click", removeQuestionForm);

  formCopyTarget.append(copyEmptyQuestionFormEl);
}

function cloneQuestionForm(currentFormCount) {
  const copyEmptyQuestionFormEl = document.getElementById("empty-form").cloneNode(true).firstElementChild;
  copyEmptyQuestionFormEl.setAttribute("class", "question-form");
  copyEmptyQuestionFormEl.removeAttribute("id");

  const regex = new RegExp("__prefix__", "g");
  copyEmptyQuestionFormEl.innerHTML = copyEmptyQuestionFormEl.innerHTML.replace(
    regex,
    currentFormCount,
  );

  totalNewForms.setAttribute("value", currentFormCount + 1);

  return copyEmptyQuestionFormEl;
}

function handleQuestionForm(questionForm) {
  const questionTypeElement = questionForm.querySelector(".question-select-type");
  handleQuestionType(questionForm);
  addEventListenerQuestionType(questionTypeElement);
}


// REMOVE

function removeQuestionForm(event) {
  if (event) {
    event.preventDefault();
  }

  const questionFormToDelete = event.target.closest(".question-form");

  if (questionFormToDelete) {
    questionFormToDelete.remove();

    const currentQuestionForms = document.querySelectorAll(".question-form");
    totalNewForms.setAttribute("value", currentQuestionForms.length - 1);
  }
}

// Handle different types of form

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
  const choicesForm = questionForm.querySelector(".question-choices-form");
  const counter = choicesForm.querySelectorAll('input[type="radio"]').length + 1;

  const createChoiceElement = (index) => {
    const choiceDiv = document.createElement("div");
    choiceDiv.classList.add("form-check");

    const input = document.createElement("input");
    input.type = "radio";
    input.classList.add("form-check-input");
    input.name = `choices_${counter}`;

    const deleteButton = document.createElement("button");
    deleteButton.textContent = "Delete";
    deleteButton.type = "button";
    deleteButton.classList.add("btn", "btn-outline-danger", "btn-sm", "mt-2");
    deleteButton.addEventListener("click", function () {
      choiceDiv.remove();
    });

    const textInput = document.createElement("input");
    textInput.type = "text";
    textInput.placeholder = `Choice ${index}`;

    choiceDiv.appendChild(input);
    choiceDiv.appendChild(textInput);
    choiceDiv.appendChild(deleteButton);

    return choiceDiv;
  };

  const fieldset = document.createElement("fieldset");
  const legend = document.createElement("legend");
  legend.textContent = "Vos choix";
  fieldset.appendChild(legend);

  for (let i = 0; i < 2; i++) {
    fieldset.appendChild(createChoiceElement(i + 1));
  }

  const addButton = document.createElement("button");
  addButton.textContent = "Add a choice";
  addButton.type = "button";
  addButton.classList.add("btn", "btn-outline-secondary", "btn-sm", "mt-2");
  addButton.addEventListener("click", function () {
    fieldset.appendChild(createChoiceElement(choicesForm.querySelectorAll('input[type="radio"]').length + 1));
  });

  choicesForm.appendChild(fieldset);
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

  switch (questionType) {
    case "short_answer":
      handleShortAnswerQuestion(questionForm);
      break;
    case "long_answer":
      handleLongAnswerQuestion(questionForm);
      break;
    case "unique_choice":
      handleUniqueChoiceQuestion(questionForm);
      break;
    // Add other cases for other type of question
    default:
      break;
  }
}

// SUBMISSION

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
      switch (questionType) {
        case "short_answer":
          handleShortAnswerSubmission(questionForm);
          break;
        case "long_answer":
          handleLongAnswerSubmission(questionForm);
          break;
        case "unique_choice":
          handleUniqueChoiceSubmission(questionForm);
          break;
        // Add other cases for other type of question
        default:
          break;
      }
    }
    let form = document.getElementById("quiz-form");
    form.submit();
  });
}

function handleShortAnswerSubmission(questionForm) {
  let shortAnswerInput = questionForm.querySelector(".short-answer-field");
  let hiddenShortAnswerInput = questionForm.querySelector(".hidden-short-answer-field");
  hiddenShortAnswerInput.value = shortAnswerInput.value;
}

function handleLongAnswerSubmission(questionForm) {
  let longAnswerInput = questionForm.querySelector(".long-answer-field");
  let hiddenLongAnswerInput = questionForm.querySelector(".hidden-long-answer-field");
  hiddenLongAnswerInput.value = longAnswerInput.value;
}

function handleUniqueChoiceSubmission(questionForm) {
  let choicesData = {};

  const radioInputs = questionForm.querySelectorAll('.form-check > input[type="radio"]');
  const textInputs = questionForm.querySelectorAll('.form-check > input[type="text"]');

  radioInputs.forEach((input, index) => {
    choicesData[textInputs[index].value] = input.checked;
  });

  let hiddenUniqueChoiceAnswerInput = questionForm.querySelector(".hidden-unique-choice-field");
  hiddenUniqueChoiceAnswerInput.value = JSON.stringify(choicesData);
}

manage_form_submission();
