/**
 * @file Esup-Pod functions for the quiz creation or edit form.
 * @since 3.7.0
 */

// Read-only globals defined in video-script.html
/*
global player
*/

// Read-only globals defined in create_edit_quiz.html
/*
global initialData
*/

document.addEventListener("DOMContentLoaded", function () {
  let addQuestionButton = document.getElementById("add-question");
  const totalNewForms = document.getElementById("id_questions-TOTAL_FORMS");
  const initialNumberForms = document.getElementById("id_questions-INITIAL_FORMS");

  let defaultQuestionForms = document.querySelectorAll(".question-form");
  for (let i = 0; i < defaultQuestionForms.length - 1; i++) {
    const defaultQuestionForm = defaultQuestionForms[i];
    handleQuestionType(defaultQuestionForm);
    handleQuestionTimestamps(defaultQuestionForm);
  }

  let questionsTypeElements = document.querySelectorAll(
    ".question-select-type",
  );
  for (let questionTypeEl of questionsTypeElements) {
    addEventListenerQuestionType(questionTypeEl);
  }

  for (let deleteInput of document.querySelectorAll('label[for*="-DELETE"]')) {
    deleteInput.parentElement.classList.add('d-none');
  }

  /**
   * Retrieves question data from the initial data based on the provided question form.
   * @param {HTMLElement} questionForm - The HTML form element representing a question.
   * @returns {Object|null} - The data associated with the question or null if no initial data is available.
   */
  function getQuestionData(questionForm) {
    if (!initialData) {
      return null;
    }
    const questionIndex = Number(questionForm.getAttribute("data-question-index"));
    return initialData.existing_questions[questionIndex];
  }

  /**
   * Adds an event listener to the question type element to handle changes.
   * @param {HTMLElement} questionTypeElement - The HTML element representing the question type.
   */
  function addEventListenerQuestionType(questionTypeElement) {
    questionTypeElement.addEventListener("change", function () {
      let questionForm = questionTypeElement.closest(".question-form");
      handleQuestionType(questionForm);
    });
  }

  addQuestionButton.addEventListener("click", addNewQuestionForm);
  let removeQuestionButtons = document.querySelectorAll(
    ".delete-question-button",
  );
  for (let removeQuestionButton of removeQuestionButtons) {
    removeQuestionButton.addEventListener("click", removeQuestionForm);
  }

  /**
   * Adds a new question form to the list of forms.
   * @param {Event} event - The triggering event.
   */
  function addNewQuestionForm(event) {
    if (event) {
      event.preventDefault();
    }

    const currentQuestionForms =
      document.getElementsByClassName("question-form");
    const currentFormCount = currentQuestionForms.length - 1;

    const formCopyTarget = document.getElementById("question-form-list");
    const copyEmptyQuestionFormEl = cloneQuestionForm(currentFormCount);

    const newQuestionTypeElement = copyEmptyQuestionFormEl.querySelector(
      ".question-select-type",
    );

    handleQuestionForm(copyEmptyQuestionFormEl);
    addEventListenerQuestionType(newQuestionTypeElement);

    const removeQuestionButton = copyEmptyQuestionFormEl.querySelector(
      ".delete-question-button",
    );
    removeQuestionButton.addEventListener("click", removeQuestionForm);

    formCopyTarget.append(copyEmptyQuestionFormEl);
  }

  /**
   * Clones an empty question form and adjusts its attributes.
   * @param {number} currentFormCount - The current count of question forms.
   * @returns {HTMLElement} - The cloned question form.
   */
  function cloneQuestionForm(currentFormCount) {
    const copyEmptyQuestionFormEl = document
      .getElementById("empty-form")
      .cloneNode(true).firstElementChild;
    copyEmptyQuestionFormEl.classList.add(
      "border",
      "rounded-3",
      "p-3",
      "mb-3",
      "question-form",
    );
    copyEmptyQuestionFormEl.removeAttribute("id");

    const regex = new RegExp("__prefix__", "g");
    copyEmptyQuestionFormEl.innerHTML =
      copyEmptyQuestionFormEl.innerHTML.replace(regex, currentFormCount);

    totalNewForms.setAttribute("value", currentFormCount + 1);
    copyEmptyQuestionFormEl.querySelector(".question-number").innerHTML =
      currentFormCount + 1;
    copyEmptyQuestionFormEl.setAttribute(
      "data-question-index",
      currentFormCount,
    );
    return copyEmptyQuestionFormEl;
  }

  /**
   * Handles a question form by updating its type and adding event listeners.
   * @param {HTMLElement} questionForm - The question form to handle.
   */
  function handleQuestionForm(questionForm) {
    const questionTypeElement = questionForm.querySelector(
      ".question-select-type",
    );
    handleQuestionType(questionForm);
    handleQuestionTimestamps(questionForm);
    addEventListenerQuestionType(questionTypeElement);
  }

  // REMOVE

  /**
   * Removes a question form from the DOM and updates the total form count.
   * @param {Event} event - The click event triggering the removal.
   */
  function removeQuestionForm(event) {
    if (event) {
      event.preventDefault();
    }

    const questionFormToDelete = event.target.closest(".question-form");

    if (questionFormToDelete) {

      // If the question already exist in Pod, we only hide in dom and send a "delete" input.
      const deleteInput = document.getElementById(`id_questions-${questionFormToDelete.getAttribute("data-question-index")}-DELETE`);
      if (deleteInput && totalNewForms.value <= initialNumberForms.value) {
        deleteInput.checked = true;
        questionFormToDelete.classList.add('d-none');
      } else {
        questionFormToDelete.remove();
        const currentQuestionForms = document.querySelectorAll(".question-form");
        totalNewForms.setAttribute("value", currentQuestionForms.length - 1);
      }
    }
  }

  // Handle different types of form

  /**
   * Handles the setup for a short answer question in the question form.
   * @param {HTMLElement} questionForm - The question form element.
   */
  function handleShortAnswerQuestion(questionForm) {
    const input = document.createElement("input");
    const inputId = "short-answer-" + questionForm.getAttribute("data-question-index");
    const label = document.createElement("label");

    input.type = "text";
    input.id = inputId;
    input.name = inputId;
    input.required = true;
    input.placeholder = gettext("The short answer");
    input.classList.add("short-answer-field", "form-control");

    label.setAttribute("for", inputId);
    label.textContent = gettext("Short answer");

    let qData = getQuestionData(questionForm);
    if (qData && qData["short_answer"] != null) {
      input.value = qData["short_answer"];
    }

    const questionChoicesForm = questionForm.querySelector(".question-choices-form");
    questionChoicesForm.appendChild(label);
    questionChoicesForm.appendChild(input);
  }

  /**
   * Handles the setup for a single choice question in the question form.
   * @param {HTMLElement} questionForm - The question form element.
   */
  function handleSingleChoiceQuestion(questionForm) {
    const choicesForm = questionForm.querySelector(".question-choices-form");
    const questionIndex = Number(questionForm.getAttribute("data-question-index"));

    const createChoiceElement = (index, choice) => {
      const choiceDiv = document.createElement("div");
      choiceDiv.classList.add("form-check", "d-flex", "align-items-center");

      const input = document.createElement("input");
      input.type = "radio";
      input.required = true;
      input.classList.add("form-check-input");
      message = gettext("Select the choice #%s as correct answer.");
      input.title = interpolate(message, [index]);
      input.name = `choice-${questionForm.getAttribute("data-question-index")}`;
      input.id = `choice-${questionForm.getAttribute("data-question-index")}-${index}`;

      const deleteButton = document.createElement("a");
      const deleteIcon = document.createElement("i");
      deleteIcon.classList.add(
        "bi",
        "bi-trash"
      );
      deleteButton.appendChild(deleteIcon);
      message = gettext("Remove choice %s");
      deleteButton.setAttribute('title', interpolate(message, [index]));
      deleteButton.setAttribute('role', 'button');
      deleteButton.classList.add(
        "btn",
        "btn-link",
        "pod-btn-social",
      );

      deleteButton.addEventListener("click", function () {
        choiceDiv.remove();
      });

      const textInput = document.createElement("input");
      textInput.id = `choice-text-${questionIndex}-${index}`;
      textInput.name = `choice-text-${questionIndex}`;
      textInput.type = "text";
      textInput.required = true;
      message = gettext("Choice #%s");
      textInput.placeholder = interpolate(message, [index]);
      textInput.classList.add("form-control", "ms-2");
      if (choice) {
        textInput.value = choice[0];
        if (choice[1]) {
          input.checked = true;
        }
      }

      const inputLabel = document.createElement("label");
      inputLabel.setAttribute("for", input.id);
      inputLabel.textContent = textInput.placeholder;
      inputLabel.classList.add("d-none");

      const textInputLabel = document.createElement("label");
      textInputLabel.setAttribute("for", textInput.id);
      textInputLabel.textContent = textInput.placeholder;
      textInputLabel.classList.add("d-none");

      choiceDiv.appendChild(inputLabel);
      choiceDiv.appendChild(input);
      choiceDiv.appendChild(textInputLabel);
      choiceDiv.appendChild(textInput);
      choiceDiv.appendChild(deleteButton);

      return choiceDiv;
    };

    const fieldset = document.createElement("fieldset");
    const legend = document.createElement("legend");
    legend.classList.add("col-form-label");
    let message = gettext("Choices for question #%s");
    legend.textContent = interpolate(message, [questionIndex+1]);
    fieldset.appendChild(legend);

    let qData = getQuestionData(questionForm);
    if (qData && qData["choices"] != null) {
      const initialChoices = Object.entries(qData["choices"]);
      for (let i = 0; i < initialChoices.length; i++) {
        fieldset.appendChild(createChoiceElement(i + 1, initialChoices[i]));
      }
    } else {
      for (let i = 0; i < 2; i++) {
        fieldset.appendChild(createChoiceElement(i + 1, null));
      }
    }

    const addButton = document.createElement("button");
    addButton.textContent = gettext("Add a choice");
    addButton.type = "button";
    addButton.classList.add("btn", "btn-primary", "btn-sm", "mt-2");
    addButton.addEventListener("click", function () {
      fieldset.appendChild(
        createChoiceElement(
          choicesForm.querySelectorAll('input[type="radio"]').length + 1,
        ),
      );
    });

    choicesForm.appendChild(fieldset);
    choicesForm.appendChild(addButton);
  }

  /**
   * Handles the setup for a multiple choice question in the question form.
   * @param {HTMLElement} questionForm - The question form element.
   */
  function handleMultipleChoiceQuestion(questionForm) {
    const choicesForm = questionForm.querySelector(".question-choices-form");
    const questionIndex = Number(questionForm.getAttribute("data-question-index"));

    const createChoiceElement = (index, choice) => {
      const choiceDiv = document.createElement("div");
      choiceDiv.classList.add("form-check", "d-flex", "align-items-center");


      const input = document.createElement("input");
      input.type = "checkbox";
      let message = gettext("Select the choice #%s as correct answer.");
      input.title = interpolate(message, [index]);
      input.classList.add("form-check-input");
      input.name = `choice-${questionIndex}`;
      input.id = `choice-${questionIndex}-${index}`;

      const deleteButton = document.createElement("a");
      message = gettext("Remove choice #%s");
      const deleteIcon = document.createElement("i");
      deleteIcon.classList.add(
        "bi",
        "bi-trash"
      );
      deleteButton.appendChild(deleteIcon);
      deleteButton.setAttribute('title', interpolate(message, [index]));
      deleteButton.setAttribute('role', 'button');
      deleteButton.classList.add(
        "btn",
        "btn-link",
        "pod-btn-social",
      );
      deleteButton.addEventListener("click", function () {
        choiceDiv.remove();
      });

      const textInput = document.createElement("input");
      textInput.type = "text";
      textInput.required = true;
      textInput.id = `choice-text-${questionForm.getAttribute("data-question-index")}-${index}`;
      textInput.name = `choice-text-${questionForm.getAttribute("data-question-index")}`;
      message = gettext("choice #%s");
      textInput.placeholder = interpolate(message, [index]);
      textInput.classList.add("form-control", "ms-2");
      if (choice) {
        textInput.value = choice[0];
        if (choice[1]) {
          input.checked = true;
        }
      }

      const inputLabel = document.createElement("label");
      inputLabel.setAttribute("for", input.id);
      inputLabel.textContent = gettext("Choice");
      inputLabel.classList.add("d-none");

      const textInputLabel = document.createElement("label");
      textInputLabel.setAttribute("for", textInput.id);
      textInputLabel.textContent = textInput.placeholder;
      textInputLabel.classList.add("d-none");

      choiceDiv.appendChild(inputLabel);
      choiceDiv.appendChild(input);
      choiceDiv.appendChild(textInputLabel);
      choiceDiv.appendChild(textInput);
      choiceDiv.appendChild(deleteButton);

      return choiceDiv;
    };

    const fieldset = document.createElement("fieldset");
    const legend = document.createElement("legend");
    legend.classList.add("col-form-label");
    let message = gettext("Choices for question #%s");
    legend.textContent = interpolate(message, [questionIndex+1]);
    fieldset.appendChild(legend);

    let qData = getQuestionData(questionForm);
    if (qData && qData["choices"] != null) {
      const initialChoices = Object.entries(qData["choices"]);
      for (let i = 0; i < initialChoices.length; i++) {
        fieldset.appendChild(createChoiceElement(i + 1, initialChoices[i]));
      }
    } else {
      for (let i = 0; i < 2; i++) {
        fieldset.appendChild(createChoiceElement(i + 1, null));
      }
    }

    const addButton = document.createElement("button");
    addButton.textContent = gettext("Add a choice");
    addButton.type = "button";
    addButton.classList.add("btn", "btn-primary", "btn-sm", "mt-2");
    addButton.addEventListener("click", function () {
      fieldset.appendChild(
        createChoiceElement(
          choicesForm.querySelectorAll('input[type="checkbox"]').length + 1,
        ),
      );
    });

    choicesForm.appendChild(fieldset);
    choicesForm.appendChild(addButton);
  }

  /**
   * Handles the setup for the specific question type in the question form.
   * @param {HTMLElement} questionForm - The question form element.
   */
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
      case "single_choice":
        handleSingleChoiceQuestion(questionForm);
        break;
      case "multiple_choice":
        handleMultipleChoiceQuestion(questionForm);
        break;
      // Add other cases for other type of question
      default:
        break;
    }
  }

  /**
   * Handles the setup for timestamps in the question form.
   * @param {HTMLElement} questionForm - The question form element.
   */
  function handleQuestionTimestamps(questionForm) {
    const startTimestampInput = questionForm.querySelector(
      ".start-timestamp-field",
    );
    const endTimestampInput = questionForm.querySelector(
      ".end-timestamp-field",
    );

    function addGetTimestampButton(htmlElement) {
      var buttonElement = document.createElement("a");
      buttonElement.classList.add(
        "get-timestamp-from-video",
        "btn",
        "btn-secondary",
        "btn-sm",
        "m-1"
      );
      buttonElement.textContent = gettext("Get time from the player");

      buttonElement.addEventListener("click", () => {
        if (!(typeof player === "undefined")) {
          htmlElement.value = Math.floor(player.currentTime());
        }
      });

      htmlElement.parentNode.insertBefore(buttonElement, htmlElement);
    }

    addGetTimestampButton(startTimestampInput);
    addGetTimestampButton(endTimestampInput);
  }

  // SUBMISSION

  /**
   * Manages the form submission process for the quiz.
   */
  function manage_form_submission() {
    let submissionButton = document.getElementById("quiz-submission-button");

    submissionButton.addEventListener("click", (event) => {
      let form = document.getElementById("quiz-form");

      if (form.reportValidity() === false) {
        showalert(
          gettext("There are errors in the form, please correct them."),
          "alert-danger",
        );
        event.preventDefault();
        event.stopPropagation();
        form.classList.add("was-validated");
      } else {
        form.classList.add("was-validated");
        if (form.dataset.morecheck) {
          window[form.dataset.morecheck](form, event);
        }
        let questionFormsList = document.querySelectorAll(".question-form");
        for (let questionForm of questionFormsList) {
          const questionType = questionForm.querySelector(
            ".question-select-type",
          ).value;
          switch (questionType) {
            case "short_answer":
              handleShortAnswerSubmission(questionForm);
              break;
            case "single_choice":
              handleSingleChoiceSubmission(questionForm);
              break;
            case "multiple_choice":
              handleMultipleChoiceSubmission(questionForm);
              break;
            // Add other cases for other type of question
            default:
              break;
          }
        }
        form.submit();
      }
    });
  }

  /**
   * Handles the submission process for short answer questions in the quiz form.
   *
   * @param {HTMLElement} questionForm - The form element representing the short answer question.
   */
  function handleShortAnswerSubmission(questionForm) {
    let shortAnswerInput = questionForm.querySelector(".short-answer-field");
    let hiddenShortAnswerInput = questionForm.querySelector(
      ".hidden-short-answer-field",
    );
    hiddenShortAnswerInput.value = shortAnswerInput.value;
  }

  /**
   * Handles the submission process for single choice questions in the quiz form.
   *
   * @param {HTMLElement} questionForm - The form element representing the single choice question.
   */
  function handleSingleChoiceSubmission(questionForm) {
    let choicesData = {};

    const radioInputs = questionForm.querySelectorAll(
      '.form-check > input[type="radio"]',
    );
    const textInputs = questionForm.querySelectorAll(
      '.form-check > input[type="text"]',
    );

    radioInputs.forEach((input, index) => {
      choicesData[textInputs[index].value] = input.checked;
    });

    let hiddenSingleChoiceAnswerInput = questionForm.querySelector(
      ".hidden-single-choice-field",
    );
    hiddenSingleChoiceAnswerInput.value = JSON.stringify(choicesData);
  }

  /**
   * Handles the submission process for multiple choice questions in the quiz form.
   *
   * @param {HTMLElement} questionForm - The form element representing the multiple choice question.
   */
  function handleMultipleChoiceSubmission(questionForm) {
    let choicesData = {};

    const checkboxInputs = questionForm.querySelectorAll(
      '.form-check > input[type="checkbox"]',
    );
    const textInputs = questionForm.querySelectorAll(
      '.form-check > input[type="text"]',
    );

    checkboxInputs.forEach((input, index) => {
      choicesData[textInputs[index].value] = input.checked;
    });

    let hiddenMultipleChoiceAnswerInput = questionForm.querySelector(
      ".hidden-multiple-choice-field",
    );
    hiddenMultipleChoiceAnswerInput.value = JSON.stringify(choicesData);
  }

  manage_form_submission();
});
