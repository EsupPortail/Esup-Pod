// Validate input type date (video date_delete)
window.onload = function () {
  // get selected lang and save it in localStorage
  let lang_btn = document.querySelector(".btn-lang.btn-lang-active");
  let lang = lang_btn ? lang_btn.textContent.trim() : "fr";
  if (
    !localStorage.getItem("lang") ||
    (localStorage.getItem("lang") && lang_btn)
  )
    localStorage.setItem("lang", lang);

  let dtf = new Intl.DateTimeFormat(lang, {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
  let input =
    document.getElementById("id_date_delete") ||
    document.querySelector('input[name="date_delete"]');

  if (input != null) {
    let given = new Date(input.value);
    const today = new Date();
    let limite = new Date();
    limite.setYear(new Date().getFullYear() + max_duration_date_delete);
    var errorlist = input.parentElement.querySelector(".errorlist");
    const error_types = ["date_too_far", "date_before_today"];
    var list_errors = [];
    if (!errorlist) {
      errorlist = document.createElement("ul");
      errorlist.classList.add("errorlist");
      input.parentNode.appendChild(errorlist);
    }

    let listener_inputchange = function () {
      given = new Date(input.value);
      list_errors = [];
      if (given > limite) {
        msg = gettext("The date must be before or equal to");
        add_error_message(`${msg} ${dtf.format(limite)}`, "date_too_far");
      } else if (given < today) {
        add_error_message(
          gettext("The deletion date can’t be earlier than today."),
          "date_before_today",
        );
      } else {
        input.parentNode.classList.remove("errors");
      }

      // Remove every obsolete message

      for (let i in error_types) {
        if (!list_errors.includes(error_types[i])) {
          if (errorlist.querySelector("." + error_types[i])) {
            errorlist.removeChild(
              errorlist.querySelector("." + error_types[i]),
            );
          }
        }
      }
    };

    // Set listener on the field and check even after reloading the page
    input.onchange = function () {
      listener_inputchange();
    };
    listener_inputchange();
  }

  /**
   * Display a validation error message on current input
   * @param {String} msg  message to be displayed
   * @param {String} type error code (added as css class)
   */
  function add_error_message(msg, type) {
    let error_message = document.createElement("li");
    // Add errors class to the input container
    input.parentNode.classList.add("errors");
    error_message.classList.add(type);
    error_message.textContent = msg;

    list_errors.push(type);
    // Insert the message at the last position in parentElement
    if (!input.parentElement.querySelector("." + type))
      errorlist.appendChild(error_message);
  }
};
