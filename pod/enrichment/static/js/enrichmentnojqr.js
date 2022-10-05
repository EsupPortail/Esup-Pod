
var id_form = "form_enrich";
function show_form(data) {
  var form = document.querySelector("#" + id_form);
  form.style.display = "none";
  form.innerHTML = data;
  fadeIn(form);

  var inputStart = document.querySelector("input#id_start");
  inputStart.insertAdjacentHTML(
    "beforebegin",
    "&nbsp;<div class='getfromvideo pull-right mb-1'><a href='' id='getfromvideo_start' class='btn btn-primary btn-sm'>" +
      gettext("Get time from the player") +
      "</a><span class='timecode'></span></div>"
  );
  var inputStart = document.querySelector("input#id_start");
  inputStart.insertAdjacentHTML(
    "beforebegin",
    "&nbsp;<div class='getfromvideo pull-right mb-1'><a href='' id='getfromvideo_end' class='btn btn-primary btn-sm'>" +
      gettext("Get time from the player") +
      "</a><span class='timecode'></span></div>"
  );
  enrich_type();
}

var showalert = function (message, alerttype) {
  document.body.append(
    '<div id="formalertdiv" class="alert ' +
      alerttype +
      ' alert-dismissible fade show" role="alert">' +
      message +
      '<button type="button" class="close" data-dismiss="alert" aria-label="' +
      gettext("Close") +
      '"><span aria-hidden="true">&times;</span></button></div>'
  );
  setTimeout(function () {
    document.getElementById("formalertdiv").remove();
  }, 5000);
};

var ajaxfail = function (data) {
  showalert(
    gettext("Error getting form.") +
      " (" +
      data +
      ") " +
      gettext("The form could not be recovered."),
    "alert-danger"
  );
  $("form.get_form").show();
  show_form("");
};

document.addEventListener("click", (e) => {
  if (e.target.id != "cancel_enrichment") return;
  document.querySelectorAll("form.get_form").style.display = "block";
  show_form("");
});

document.addEventListener("submit", (e) => {
  if (!e.target.classList.contains("get_form")) return;
  e.preventDefault();
  var jqxhr = "";
  var action = e.target.querySelector("input[name=action]").value;

  sendandgetform(e.target, action);
});
document.addEventListener("submit", (e) => {
  if (!e.target.classList.contains("form_save")) return;
  e.preventDefault();
  var jqxhr = "";

  var action = e.target.querySelector("input[name=action]").value;
  sendform(e.target, action);
});

var sendandgetform = async function (elt, action) {
  document.querySelector("form.get_form").style.display = "none";
  let token = elt.querySelector("input[name=csrfmiddlewaretoken]").value;
  if (action == "new") {
    url = window.location.href;
    headers = {
      "Content-Type": "application/json",
      "X-CSRFToken": token,
    };
    data = JSON.stringify({
      action: action,
    });

    await fetch(url, {
      method: "POST",
      headers: headers,
      body: data,
      dataType: "html",
    })
      .then((response) => response.text())
      .then((data) => {
        if (data.indexOf(id_form) == -1) {
          showalert(
            gettext("You are no longer authenticated. Please log in again."),
            "alert-danger"
          );
        } else {
          show_form(data);
        }
      })
      .catch((error) => {
        ajaxfail(error);
      });
  }
  if (action == "modify") {
    var id = elt.querySelector("input[name=id]").value;
    url = window.location.href;
    let token = elt.querySelector("input[name=csrfmiddlewaretoken]").value;
    headers = {
      "Content-Type": "application/json",
      "X-CSRFToken": token,
    };
    data = JSON.stringify({
      action: action,
      id: id,
    });

    await fetch(url, {
      method: "POST",
      headers: headers,
      body: data,
      dataType: "html",
    })
      .then((response) => response.text())
      .then((data) => {
        if (data.indexOf(id_form) == -1) {
          showalert(
            gettext("You are no longer authenticated. Please log in again."),
            "alert-danger"
          );
        } else {
          show_form(data);
          elt.classList.add("info");
        }
      })
      .catch((error) => {
        ajaxfail(error);
      });
  }

  if (action == "delete") {
    var id = elt.querySelector("input[name=id]").value;
    url = window.location.href;
    let token = elt.querySelector("input[name=csrfmiddlewaretoken]").value;
    headers = {
      "Content-Type": "application/json",
      "X-CSRFToken": token,
    };
    data = JSON.stringify({
      action: action,
      id: id,
    });

    await fetch(url, {
      method: "POST",
      headers: headers,
      body: data,
      dataType: "html",
    })
      .then((response) => response.text())
      .then((data) => {
        if (data.indexOf("list_enrichment") == -1) {
          showalert(
            gettext("You are no longer authenticated. Please log in again."),
            "alert-danger"
          );
        } else {
          location.reload();
        }
      })
      .catch((error) => {
        ajaxfail(error);
      });
  }
};

var sendform = async function (elt, action) {
  if (action == "save") {
    document
      .querySelector(".form-help-inline")
      .parentNode.querySelectorAll.forEach((elt) => {
        elt.classList.remove("has-error");
      });
    document.querySelector(".form-help-inline").remove();
    if (verify_fields() && verify_end_start_items() && overlaptest()) {
      let form_enrich = document.querySelector("form#form_enrich");
      var data_form = new FormData(form_chapter);
      var data = Object.fromEntries(data_form.entries());

      let token = elt.querySelector("input[name=csrfmiddlewaretoken]").value;
      let url = window.location.href;
      let headers = {
        "Content-Type": "application/json",
        "X-CSRFToken": token,
      };
      data = JSON.stringify({
        action: action,
        data: data,
      });

      await fetch(url, {
        method: "POST",
        headers: headers,
        body: data,
        dataType: "html",
      })
        .then((response) => response.text())

        .then((data) => {
          if (
            data.indexOf("list_enrichment") == -1 &&
            data.indexOf("form") == -1
          ) {
            showalert(
              gettext("You are no longer authenticated. Please log in again."),
              "alert-danger"
            );
          } else {
            data = JSON.parse(data);
            if (data.errors) {
              show_form(data.form);
              document.querySelector("form#form_enrich").style.display =
                "block";
            } else {
              location.reload();
            }
          }
        });
    } else {
      showalert(
        gettext("One or more errors have been found in the form."),
        "alert-danger"
      );
    }
  }
  if (action == "import") {
    var file = elt.querySelector("input[name=file]").value;
    let url = window.location.href;
    let token = elt.querySelector("input[name=csrfmiddlewaretoken]").value;
    let headers = {
      "Content-Type": "application/json",
      "X-CSRFToken": token,
    };
    data = JSON.stringify({
      action: action,
      file: file,
    });
    await fetch(url, {
      method: "POST",
      headers: headers,
      body: data,
      dataType: "html",
    })
      .then((response) => response.text())
      .then((data) => {
        if (data.indexOf("list_enrichment") == -1) {
          showalert(
            gettext("You are no longer authenticated. Please log in again."),
            "alert-danger"
          );
        } else {
          location.reload();
        }
      })
      .catch((error) => {
        ajaxfail(error);
      });
  }
};
/*** Function show the item selected by type field ***/
document.addEventListener("change", (e) => {
  if (e.target.id == "id_type") return;
  enrich_type();
});

/*** Display element of form enrich ***/
Number.prototype.toHHMMSS = function () {
  var seconds = Math.floor(this),
    hours = Math.floor(seconds / 3600);
  seconds -= hours * 3600;
  var minutes = Math.floor(seconds / 60);
  seconds -= minutes * 60;

  if (hours < 10) {
    hours = "0" + hours;
  }
  if (minutes < 10) {
    minutes = "0" + minutes;
  }
  if (seconds < 10) {
    seconds = "0" + seconds;
  }
  return hours + ":" + minutes + ":" + seconds;
};

function get_form(data) {
  var form = document.getElementById("#form_enrich");
  form.style.display = "none";
  form.innerHTML = data;
  fadeIn(form);
  var inputStart = document.querySelector("input#id_start");
  inputStart.insertAdjacentHTML(
    "beforebegin",
    "&nbsp;<div class='getfromvideo pull-right mb-1'><a href='' id='getfromvideo_start' class='btn btn-primary btn-sm'>" +
      gettext("Get time from the player") +
      "</a><span class='timecode'></span></div>"
  );
  var inputStart = document.querySelector("input#id_start");
  inputStart.insertAdjacentHTML(
    "beforebegin",
    "&nbsp;<div class='getfromvideo pull-right mb-1'><a href='' id='getfromvideo_end' class='btn btn-primary btn-sm'>" +
      gettext("Get time from the player") +
      "</a><span class='timecode'></span></div>"
  );
  enrich_type();
  manageResize();
}
function enrich_type() {
  document
    .getElementById("id_image")
    .parentNode.querySelectorAll("div.form-group")
    .forEach((elt) => {
      elt.style.display = "none";
    });
  document
    .querySelector("textarea#id_richtext")
    .parentNode.querySelector("div.form-group").style.display = "none";

  document
    .getElementById("id_weblink")
    .parentNode.querySelectorAll("div.form-group")
    .forEach((elt) => {
      elt.style.display = "none";
    });

  document
    .getElementById("id_document")
    .parentNode.querySelectorAll("div.form-group")
    .forEach((elt) => {
      elt.style.display = "none";
    });

  document
    .getElementById("id_embed")
    .parentNode.querySelectorAll("div.form-group")
    .forEach((elt) => {
      elt.style.display = "none";
    });
  var val = document.querySelector("select#id_type").value;
  if (val != "") {
    var form = document.getElementById("form_enrich");
    form.querySelectorAll('[id^="id_' + val + '"]').forEach((elt) => {
      elt.parentNode.querySelector("div.form-group").style.display = "block";
    });
  }
}
document.addEventListener("change", (e) => {
  if (e.target.id == "id_start") return;

  e.target.parentNode.querySelector(
    "span.getfromvideo span.timecode"
  ).innerHTML = " " + parseInt($(this).val()).toHHMMSS();
});
document.addEventListener("change", (e) => {
  if (e.target.id == "id_end") return;
  e.target.parentNode.querySelector(
    "span.getfromvideo span.timecode"
  ).innerHTML = " " + parseInt($(this).val()).toHHMMSS();
});
document.addEventListener("click", "#page-video .getfromvideo a", function (e) {
  if (e.target.parentNode.classList.contains("getfromvideo")) return;
  e.preventDefault();
  if (!(typeof player === "undefined")) {
    if (e.target.getAttribute("id") == "getfromvideo_start") {
      let inputStart = document.querySelector("input#id_start");
      inputStart.value = parseInt(player.currentTime());
      inputStart.change();
    } else {
      let inputEnd = document.querySelector("input#id_end");
      inputEnd.value = parseInt(player.currentTime());
      inputEnd.change();
    }
  }
});
/*** Verify if value of field respect form field ***/
function verify_fields() {
  var error = false;
  if (
    document.getElementById("id_title").value == "" ||
    document.getElementById("id_title").value.length < 2 ||
    document.getElementById("id_title").value.length > 100
  ) {
    let inputTitle = document.querySelector("input#id_title");
    inputTitle.insertAdjacentHTML(
      "beforebegin",
      "<span class='form-help-inline'>&nbsp;&nbsp;" +
        gettext("Please enter a title from 2 to 100 characters.") +
        "</span>"
    );
    inputTitle.parentNode.querySelectorAll("div.form-group").forEach((elt) => {
      elt.classList.add("has-error");
    });

    error = true;
  }
  if (
    document.getElementById("id_start").value == "" ||
    document.getElementById("id_start").value < 0 ||
    document.getElementById("id_start").value >= video_duration
  ) {
    let inputStart = document.querySelector("input#id_start");
    inputStart.insertAdjacentHTML(
      "beforebegin",
      "<span class='form-help-inline'>&nbsp; &nbsp;" +
        gettext("Please enter a correct start from 0 to ") +
        (video_duration - 1) +
        "</span>"
    );
    inputStart.parentNode.querySelectorAll("div.form-group").forEach((elt) => {
      elt.classList.add("has-error");
    });

    error = true;
  }
  if (
    document.getElementById("id_end").value == "" ||
    document.getElementById("id_end").value <= 0 ||
    document.getElementById("id_end").value > video_duration
  ) {
    let inputEnd = document.querySelector("input#id_end");
    inputEnd.insertAdjacentHTML(
      "beforebegin",
      "<span class='form-help-inline'>&nbsp; &nbsp;" +
        gettext("Please enter a correct end from 1 to ") +
        video_duration +
        "</span>"
    );
    inputEnd.parentNode.querySelectorAll("div.form-group").forEach((elt) => {
      elt.classList.add("has-error");
    });

    error = true;
  }
  switch (document.getElementById("id_type").value) {
    case "image":
      let img = document.getElementById("id_image_thumbnail_img");
      if (img.src == "/static/filer/icons/nofile_48x48.png") {
        //check with id_image value
        img.insertAdjacentElement(
          "beforebegin",
          "<span class='form-help-inline'>&nbsp; &nbsp;" +
            gettext("Please enter a correct image.") +
            "</span>"
        );
        img.parentNode.querySelectorAll("div.form-group").forEach((elt) => {
          elt.classList.add("has-error");
        });

        error = true;
      }
      break;
    case "richtext":
      let richtext = document.getElementById("id_richtext");
      if (richtext.value == "") {
        richtext.insertAdjacentHTML(
          "beforebegin",
          "<span class='form-help-inline'>&nbsp; &nbsp;" +
            gettext("Please enter a correct richtext.") +
            "</span>"
        );
        richtext.parentNode
          .querySelectorAll("div.form-group")
          .forEach((elt) => {
            elt.classList.add("has-error");
          });

        error = true;
      }
      break;
    case "weblink":
      let weblink = document.getElementById("id_weblink");
      if (weblink.value == "") {
        weblink.insertAdjacentHTML(
          "beforebegin",
          "<span class='form-help-inline'>&nbsp; &nbsp;" +
            gettext("Please enter a correct weblink.") +
            "</span>"
        );
        weblink.parentNode.querySelectorAll("div.form-group").forEach((elt) => {
          elt.classList.add("has-error");
        });

        error = true;
      } else {
        if (weblink.value > 200) {
          weblink.insertAdjacentHTML(
            "beforebegin",
            "<span class='form-help-inline'>&nbsp; &nbsp;" +
              gettext("Weblink must be less than 200 characters.") +
              "</span>"
          );
          weblink.parentNode
            .querySelectorAll("div.form-group")
            .forEach((elt) => {
              elt.classList.add("has-error");
            });

          error = true;
        }
      }
      break;
    case "document":
      let documentD = document.getElementById("id_document");
      if (documentD.src == "/static/filer/icons/nofile_48x48.png") {
        //check with id_document value
        documentD.insertAdjacentHTML(
          "beforebegin",
          "<span class='form-help-inline'>&nbsp; &nbsp;" +
            gettext("Please select a document.") +
            "</span>"
        );
        documentD.parentNode
          .querySelectorAll("div.form-group")
          .forEach((elt) => {
            elt.classList.add("has-error");
          });

        error = true;
      }
      break;
    case "embed":
      let embed = document.getElementById("id_embed");
      if (embed.value == "") {
        embed.insertAdjacentHTML(
          "beforebegin",
          "<span class='form-help-inline'>&nbsp; &nbsp;" +
            gettext("Please enter a correct embed.") +
            "</span>"
        );
        embed.parentNode.querySelectorAll("div.form-group").forEach((elt) => {
          elt.classList.add("has-error");
        });

        error = true;
      } else {
        if (embed.value > 200) {
          embed.insertAdjacentHTML(
            "beforebegin",
            "<span class='form-help-inline'>&nbsp; &nbsp;" +
              gettext("Embed field must be less than 200 characters.") +
              "</span>"
          );

          embed.parentNode.querySelectorAll("div.form-group").forEach((elt) => {
            elt.classList.add("has-error");
          });

          error = true;
        }
      }
      break;
    default:
      let inputType = document.querySelector("input#id_type");
      inputType.insertAdjacentHTML(
        "beforebegin",
        "<span class='form-help-inline'>&nbsp; &nbsp;" +
          gettext("Please enter a type in index field.") +
          "</span>"
      );
      inputType.parentNode.querySelectorAll("div.form-group").forEach((elt) => {
        elt.classList.add("has-error");
      });

      error = true;
  }
  return !error;
}
/***  Verify if fields end and start are correct ***/
function verify_end_start_items() {
  var msg = "";
  new_start = parseInt(document.getElementById("id_start").value);
  new_end = parseInt(document.getElementById("id_end").value);
  if (new_start > new_end) {
    msg = gettext("The start field value is greater than the end field one.");
  } else if (new_end > video_duration) {
    msg = gettext("The end field value is greater than the video duration.");
  } else if (new_start == new_end) {
    msg = gettext("End field and start field cannot be equal.");
  }
  if (msg) {
    return msg;
  }
  return true;
}
/*** Verify if there is a overlap with over enrich***/
function overlaptest() {
  //var video_list_enrich=[];
  var new_start = parseInt(document.getElementById("id_start").value);
  var new_end = parseInt(document.getElementById("id_end").value);
  var id = document.getElementById("id_enrich").value;
  var msg = "";
  document.querySelectorAll("ul#slides li").forEach((e) => {
    var data_start = parseInt(e.getAttribute("data-start"));
    var data_end = parseInt(e.getAttribute("data-end"));
    if (
      id != e.getAttribute("data-id") &&
      !(
        (new_start < data_start && new_end <= data_start) ||
        (new_start >= data_end && new_end > data_end)
      )
    ) {
      var text =
        gettext("There is an overlap with the enrichment ") +
        '"' +
        e.getAttribute("data-title") +
        '"';
      text += ", " + gettext("please change start and/or end values.");
      msg += '<div class="alert alert-warning">' + text + "</div>";
    }
  });
  if (msg) {
    return msg;
  }
  return true;
}
