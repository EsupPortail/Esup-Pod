/**
 * @file Esup-Pod Completion scripts.
 */

// Read-only globals defined in main.js
/*
global fadeIn
*/

// Video form
//var num = 0;
var name = "";

function show_form(data, form) {
  let form_el = document.getElementById(form);
  form_el.style.display = "none";
  form_el.innerHTML = data;
  const scripts = form_el.querySelectorAll("script");
  if (scripts.length > 0) {
    scripts.forEach((item) => {
      if (item.src) {
        // external script
        let script = document.createElement("script");
        script.src = item.src;
        document.body.appendChild(script);
      } else {
        // inline script
        (0, eval)(item.innerHTML);
      }
    });
  }
  fadeIn(form_el);
  if (form === "form_track")
    document.getElementById("form_track").style.width = "100%";
}

var ajaxfail = function (data, form) {
  showalert(
    gettext("Error getting form.") +
      " (" +
      data +
      ") " +
      gettext("The form could not be recovered."),
    "alert-danger",
  );
};

//  Hide/Show the add hyperlink button
document.getElementById("add-hyperlink-btn").addEventListener("click", function () {
  document.getElementById("hyperlink-form").style.display = "block";
  this.style.display = "none";
});

//SUBMIT

document.addEventListener("submit", (e) => {
  if (
    e.target.id !== "form_new_contributor" &&
    e.target.id !== "form_contributor" &&
    e.target.id !== "form_new_speaker" &&
    e.target.id !== "form_speaker" &&
    e.target.id !== "form_new_document" &&
    e.target.id !== "form_document" &&
    e.target.id !== "form_new_track" &&
    e.target.id !== "form_new_overlay" &&
    e.target.id !== "form_new_hyperlink" &&
    !e.target.matches(".form_change") &&
    !e.target.matches(".form_modif") &&
    !e.target.matches(".form_delete")
  )
    return;

  e.preventDefault();
  // var jqxhr = "";
  var exp = /_([a-z]*)\s?/g;
  var id_form = e.target.getAttribute("id");
  var name_form = "";
  var result_regexp = "";
  if (id_form == undefined) {
    var form_class = e.target
      .querySelector("input[type=submit]")
      .getAttribute("class");
    result_regexp = exp.exec(form_class);
    name_form = result_regexp[1];
  } else {
    result_regexp = id_form.split(exp);
    name_form = result_regexp[result_regexp.length - 2];
  }
  var form = "form_" + name_form;
  var list = "list-" + name_form;
  var action = e.target.querySelector("input[name=action]").value;
  sendAndGetForm(e.target, action, name_form, form, list)
    .then(() => "")
    .catch((e) => console.log("error", e));
});

/**
 * Send and get form.
 *
 * @param {HTMLElement} elt - HTML element.
 * @param {string} action - Action.
 * @param {string} name - Name.
 * @param {string} form - Form.
 * @param {string} list - List.
 *
 * @return {Promise<void>} The form promise.
 */
var sendAndGetForm = async function (elt, action, name, form, list) {
  var href = elt.getAttribute("action");
  let url = window.location.origin + href;
  let token = elt.csrfmiddlewaretoken.value;

  if (action === "new" || action === "form_save_new") {
    document.getElementById(form).innerHTML =
      '<div style="width:100%; margin: 2rem;"><div class="lds-ellipsis"><div></div><div></div><div></div><div></div></div></div>';

    document
      .querySelectorAll(
        `#card-completion-tips div:not(#${name}-info) .collapse`,
      )
      .forEach((collapsable) => {
        bootstrap.Collapse.getOrCreateInstance(collapsable, {
          toggle: false,
        }).hide();
      });
    /* Display associated help in side menu */
    var compInfo = document.querySelector(`#${name}-info>.collapse`);
    try {
      bootstrap.Collapse.getOrCreateInstance(compInfo).show();
    } catch (e) {
      // do nothing
    }

    let form_data = new FormData(elt);

    await fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": token,
        "X-Requested-With": "XMLHttpRequest",
      },

      body: form_data,
      datatype: "html",
    })
      .then((response) => response.text())
      .then((data) => {
        //parse data into html and log it
        if (data.indexOf(form) === -1) {
          showalert(
            gettext(
              "You are no longer authenticated. Please log in again.",
              "alert-danger",
            ),
          );
        } else {
          show_form(data, form);
        }
      })
      .catch((error) => {
        ajaxfail(error, form);
        document.querySelector("form.form_change").style.display = "block";
        document.querySelector("form.form_modif").style.display = "block";
        document.querySelector("form.form_delete").style.display = "block";
        document.querySelector("form.form_new").style.display = "block";
        document.getElementById(form).textContent = "";
      });

    const formClasses = [
      "form_new",
      "form_change",
      "form_modif",
      "form_delete",
    ];
    formClasses.forEach((formClass) => {
      document.querySelectorAll(`form.${formClass}`).forEach((form) => {
        if (form) form.style.display = "none";
      });
    });
  }
  if (action == "modify" || action == "form_save_modify") {
    let id = elt.querySelector("input[name=id]").value;
    let form_data = new FormData();
    form_data.append("action", action);
    form_data.append("id", id);

    await fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": token,
        "X-Requested-With": "XMLHttpRequest",
      },
      body: form_data,
    })
      .then((response) => response.text())
      .then((data) => {
        if (data.indexOf(form) === -1) {
          showalert(
            gettext(
              "You are no longer authenticated. Please log in again.",
              "alert-danger",
            ),
          );
        } else {
          show_form(data, form);
        }
      })
      .catch((error) => {
        ajaxfail(error, form);
        document.querySelector("form.form_modif").style.display = "block";
        document.querySelector("form.form_delete").style.display = "block";
        document.querySelector("form.form_new").style.display = "block";
        document.getElementById(form).textContent = "";
      });

    document.querySelector("a.title").style.display = "none";
    // hide_others_sections(name);
  }
  if (action === "delete") {
    var deleteConfirm = new bootstrap.Modal(
      document.getElementById("deleteConfirmModal"),
    );
    var messageElement = document.getElementById("modalMessage");

    let confirmationMessage;
    if (name === "track") {
      confirmationMessage = gettext(
        "Are you sure you want to delete this file?",
      );
    } else if (name === "contributor") {
      confirmationMessage = gettext(
        "Are you sure you want to delete this contributor?",
      );
    } else if (name === "speaker") {
      confirmationMessage = gettext(
        "Are you sure you want to delete this speaker?",
      );
    } else if (name === "document") {
      confirmationMessage = gettext(
        "Are you sure you want to delete this document?",
      );
    } else if (name === "overlay") {
      confirmationMessage = gettext(
        "Are you sure you want to delete this overlay?",
      );
    } else if (name === "hyperlink") {
      confirmationMessage = gettext(
        "Are you sure you want to delete this hyperlink?",
      );
    }

    messageElement.innerText = confirmationMessage;
    deleteConfirm.show();

    var confirmButton = document.getElementById("confirmDeleteButton");
    var newConfirmButton = confirmButton.cloneNode(true);
    confirmButton.replaceWith(newConfirmButton);
    confirmButton = newConfirmButton;

    confirmButton.addEventListener(
      "click",
      async function () {
        let id = elt.querySelector("input[name=id]").value;
        url = window.location.origin + href;
        token = document.querySelector("input[name=csrfmiddlewaretoken]").value;
        let form_data = new FormData();
        form_data.append("action", action);
        form_data.append("id", id);

        await fetch(url, {
          method: "POST",
          headers: {
            "X-CSRFToken": token,
            "X-Requested-With": "XMLHttpRequest",
          },
          body: form_data,
        })
          .then((response) => response.text())
          .then((data) => {
            data = JSON.parse(data);
            if (data.list_data) {
              refresh_list(data, form, list);
            } else {
              showalert(
                gettext(
                  "You are no longer authenticated. Please log in again.",
                  "alert-danger",
                ),
              );
            }
          })
          .catch((error) => {
            ajaxfail(error, form);
          });
        deleteConfirm.hide();
      },
      { once: true },
    );
  }
  if (action == "save") {
    //let form_group = document.querySelector(".form-help-inline");
    //form_group.closest("div.form-group").classList.remove("has-error");

    //document.querySelector(".form-help-inline").remove();
    if (verify_fields(form)) {
      //var form_el = document.getElementById(form);
      var form_el = document.querySelector(`form#${form}`);
      let data_form = new FormData(form_el);
      let url = window.location.origin + href;
      let token = document.querySelector(
        "input[name=csrfmiddlewaretoken]",
      ).value;

      await fetch(url, {
        method: "POST",
        headers: {
          "X-CSRFToken": token,
          "X-Requested-With": "XMLHttpRequest",
        },
        body: data_form,
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.list_data || data.form) {
            if (data.errors) {
              document.getElementById("formalertdiv").remove();
              show_form(data.form, form);
            } else {
              refresh_list(data, form, list);
              //window.scrollTop(100);
              window.scrollTo(0, 100);
            }
          } else {
            showalert(
              gettext(
                "You are no longer authenticated. Please log in again.",
                "alert-danger",
              ),
            );
          }
        })
        .catch((error) => {
          ajaxfail(error, form);
        });
    }
  }
};

// Hide others sections
/*function hide_others_sections(name_form) {
  var allElements = document.querySelectorAll("a.title.active");
  var sections = [];
  let form = document.querySelector('a[id="section_' + name_form + '"]');

  allElements.forEach(function (element) {
    if (element.id !== form.id) {
      sections.push(element);
    }
  });
  if (sections.length > 0) {
    sections.forEach(function (element) {
      slideUp(element.parentNode.nextElementSibling);
      element.classList.remove("active");
    });
    for (let i = 0; i < sections.length; i++) {
      var section = sections[i];
      var text = section.text;
      var name_section = "'" + text.replace(/\s/g, "") + "'";
      section.title =
        gettext("Display") + " " + name_section + " " + gettext("section");
      section.firstElementChild.className = "glyphicon glyphicon-chevron-down";
    }
  }
}*/

// Refreshes the list
function refresh_list(data, form, list) {
  document.getElementById(form).innerHTML = "";
  //document.querySelector("form.form_new").style.display = "block";
  document.querySelectorAll("form").forEach(function (element) {
    element.style.display = "block";
  });

  if (data.player) {
    document.getElementById("enrich_player").innerHTML = data.player;
  }
  document.getElementById(list).innerHTML = data.list_data;
}

// Check fields
function verify_fields(form) {
  var error = false;
  if (form == "form_contributor") {
    if (
      document.getElementById("id_name").value == "" ||
      document.getElementById("id_name").value.length < 2 ||
      document.getElementById("id_name").length > 200
    ) {
      let id_name = document.getElementById("id_name");
      id_name.insertAdjacentHTML(
        "afterend",
        "<span class='form-help-inline'>&nbsp;&nbsp;" +
          gettext("Please enter a name from 2 to 100 caracteres.") +
          "</span>",
      );
      let form_group = input.closest("div.form-group");

      form_group.classList.add("has-error");

      error = true;
    }
    if (document.getElementById("id_weblink").value.length >= 200) {
      let id_weblink = document.getElementById("id_weblink");
      id_weblink.insertAdjacentHTML(
        "afterend",
        "<span class='form-help-inline'>&nbsp;&nbsp;" +
          gettext("You cannot enter a weblink with more than 200 caracteres.") +
          "</span>",
      );
      let form_group = id_weblink.closest("div.form-group");
      form_group.classList.add("has-error");

      error = true;
    }
    if (document.getElementById("id_role").value == "") {
      let id_role = document.getElementById("id_role");
      id_role.insertAdjacentHTML(
        "afterend",
        "<span class='form-help-inline'>&nbsp;&nbsp;" +
          gettext("Please enter a role.") +
          "</span>",
      );
      let form_group = id_role.closest("div.form-group");
      form_group.classList.add("has-error");
      error = true;
    }
    var id = parseInt(document.getElementById("id_contributor").value, 10);
    var new_role = document.getElementById("id_role").value;
    var new_name = document.getElementById("id_name").value;
    document.querySelectorAll("#table-contributor tbody > tr").forEach((tr) => {
      if (
        id != tr.querySelector("input[name=id]").value &&
        tr.querySelector("td[class=contributor-name]").innerHTML == new_name &&
        tr.querySelector("td[class=contributor_role]").innerHTML == new_role
      ) {
        var text = gettext(
          "There is already a contributor with this same name and role in the list.",
        );
        showalert(text, "alert-danger");
        error = true;
      }
    });
  } else if (form == "form_track") {
    var element = document.getElementById("id_kind");
    var value = element.options[element.selectedIndex].value
      .trim()
      .toLowerCase();
    var kind = element.options[element.selectedIndex].text.trim().toLowerCase();
    if (value !== "subtitles" && value !== "captions") {
      let id_kind = document.getElementById("id_kind");
      id_kind.insertAdjacentHTML(
        "afterend",
        "<span class='form-help-inline'>" +
          gettext("Please enter a correct kind.") +
          "</span>",
      );
      let form_group = id_kind.closest("div.form-group");
      form_group.classList.add("has-error");

      error = true;
    }
    element = document.getElementById("id_lang");
    var lang = element.options[element.selectedIndex].value
      .trim()
      .toLowerCase();
    if (element.options[element.selectedIndex].value.trim() === "") {
      let id_lang = document.getElementById("id_lang");
      id_lang.insertAdjacentHTML(
        "afterend",
        "<span class='form-help-inline'>" +
          gettext("Please select a language.") +
          "</span>",
      );
      let form_group = id_lang.closest("div.form-group");
      form_group.classList.add("has-error");

      error = true;
    }
    var file_abs_path = document
      .getElementById("fileinput_id_src")
      .getElementsByTagName("a")[0]
      .getAttribute("href");
    let id_src = document.getElementById("id_src");
    if (document.getElementById("id_src").value.trim() === "") {
      id_src.insertAdjacentHTML(
        "afterend",
        "<span class='form-help-inline'>" +
          gettext("Please specify a track file.") +
          "</span>",
      );
      let form_group = id_src.closest("div.form-group");
      form_group.classList.add("has-error");
      error = true;
    } else if (!file_abs_path.match(/\.vtt$/)) {
      id_src.insertAdjacentHTML(
        "afterend",
        "<span class='form-help-inline'>" +
          gettext("Only .vtt format is allowed.") +
          "</span>",
      );
      let form_group = id_src.closest("div.form-group");
      form_group.classList.add("has-error");
      error = true;
    }
    var is_duplicate = false;
    var file_name = file_abs_path.match(/([\w\d_-]+)(\.vtt)/)[1].toLowerCase();
    document
      .querySelectorAll(".grid-list-track .track-kind.kind")
      .forEach((elt) => {
        if (
          kind === elt.textContent.trim().toLowerCase() &&
          lang ===
            elt.parentNode
              .querySelector("#" + elt.get("id") + ".track-kind.lang")
              .textContent.trim()
              .toLowerCase() &&
          file_name ===
            elt.parentNode
              .querySelector("#" + elt.get("id") + ".track-kind.file")
              .textContent.trim()
              .split(" ")[0]
              .toLowerCase()
        ) {
          is_duplicate = true;
          return false;
        }
      });
    if (is_duplicate) {
      id_src.insertAdjacentHTML(
        "afterend",
        "<span class='form-help-inline'>" +
          gettext(
            "There is already a track with the same kind and language in the list.",
          ) +
          "</span>",
      );
      let form_group = id_src.closest("div.form-group");
      form_group.classList.add("has-error");
      error = true;
    }
  } else if (form == "form_document") {
    if (document.getElementById("id_document").value == "") {
      let id_document = document.getElementById("id_document");
      id_document.insertAdjacentHTML(
        "afterend",
        "<span class='form-help-inline'>" +
          gettext("Please select a document") +
          "</span>",
      );
      //   if (
      //     document
      //       .getElementById("id_document_thumbnail_img")
      //       .getAttribute("src") == "/static/icons/nofile_48x48.png"
      //   ) {
      //     let id_document_thumbnail = document.getElementById(
      //       "id_document_thumbnail_img",
      //     );
      //     id_document_thumbnail.insertAdjacentHTML(
      //       "afterend",
      //       "<span class='form-help-inline'>" +
      //         gettext("Please select a document") +
      //         "</span>",
      //     );
      let form_group = id_document.closest("div.form-group");
      form_group.classList.add("has-error");

      error = true;
    }
    let idDocumentInput = document
      .querySelector(`form#${form}`)
      .querySelector("input[id=id_document]");
    let idInstanceDocumentInput = document
      .querySelector(`form#${form}`)
      .querySelector("input[id=id-instance-document]");

    let id_document = idDocumentInput ? idDocumentInput.value : null;
    let id_instance_document = idInstanceDocumentInput
      ? idInstanceDocumentInput.value
      : null;

    if (id_document) {
      document.querySelectorAll("#table-document tbody > tr").forEach((tr) => {
        let trInstanceId = tr.getAttribute("data-id-instance");
        let trDocumentTd = tr.querySelector(".document_name");
        let trDocumentId = trDocumentTd
          ? trDocumentTd.getAttribute("data-id-document")
          : null;

        if (
          trDocumentId === id_document &&
          trInstanceId !== id_instance_document
        ) {
          let text = gettext("There is already the same document in the list.");
          showalert(text, "alert-danger");
          error = true;
        }
      });
    }
  } else if (form == "form_overlay") {
    var tags = /<script.+?>|<iframe.+?>/;
    if (tags.exec(document.getElementById("id_content").value) != null) {
      let id_content = document.getElementById("id_content");
      id_content.insertAdjacentHTML(
        "afterend",
        "<span class='form-help-inline'>&nbsp;&nbsp;" +
          gettext("Iframe and Script tags are not allowed.") +
          "</span>",
      );
      let form_group = id_content.closest("div.form-group");
      form_group.forEach(function (element) {
        element.classList.add("has-error");
      });
      error = true;
    }
  } else if (form == "form_speaker") {
    id_job = document
      .querySelector(`form#${form}`)
      .querySelector("#id_job").value;
    document.querySelectorAll("#table-speaker tbody > tr").forEach((tr) => {
      let trId = tr.id;
      let currentId = trId.replace("job_", "");

      if (currentId === id_job) {
        var text = gettext(
          "There is already the same speaker with this job in the list.",
        );
        showalert(text, "alert-danger");
        error = true;
      }
    });
  }
  return !error;
}
