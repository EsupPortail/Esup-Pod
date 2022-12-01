var id_form = "form_enrich";
function show_form(data) {
  var form = document.getElementById(id_form);
  form.style.display = "none";
  //form.innerHTML = data;

  form.innerHTML = data;
  form.querySelectorAll("script").forEach((item) => {
    if (item.src) {
      // external script

      let script = document.createElement("script");
      script.src = item.src;
      if (script.src.includes("filewidget.js"))
        document.body.appendChild(script);
    } else {
      if (item.id == "filewidget_script") (0, eval)(item.innerHTML);
    }
  });

  fadeIn(form);

  var inputStart = document.getElementById("id_start");
  if (!inputStart) return;
  inputStart.insertAdjacentHTML(
    "beforebegin",
    "&nbsp;<div class='getfromvideo pull-right mb-1'><a href='' id='getfromvideo_start' class='btn btn-primary btn-sm'>" +
      gettext("Get time from the player") +
      "</a><span class='timecode'></span></div>"
  );
  var inputEnd = document.getElementById("id_end");
  if (!inputEnd) return;
  inputEnd.insertAdjacentHTML(
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
  document.querySelectorAll("form.get_form").forEach((form)=>{
    form.style.display = "block";
  })
  

  show_form("");
};

document.addEventListener("click", (e) => {
  if (e.target.id != "cancel_enrichment") return;
  document.querySelectorAll("form.get_form").forEach((form)=> {
    form.style.display = "block";
    show_form("");
  })
  
  
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
  // document.querySelector("form.get_form").style.display = "none";
  let token = elt.querySelector("input[name=csrfmiddlewaretoken]").value;
  if (action == "new") {
    url = window.location.href;
    headers = {
      "X-CSRFToken": token,
      "X-Requested-With": "XMLHttpRequest",
    };

    let form_data = new FormData();
    form_data.append("action", action);
    await fetch(url, {
      method: "POST",
      headers: headers,
      body: form_data,
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
        console.log(error);
        ajaxfail(error);
      });
  }
  if (action == "modify") {
    var id = elt.querySelector("input[name=id]").value;
    url = window.location.href;
    let token = elt.querySelector("input[name=csrfmiddlewaretoken]").value;
    headers = {
      "X-CSRFToken": token,
      "X-Requested-With": "XMLHttpRequest",
    };

    form_data = new FormData();
    form_data.append("action", action);
    form_data.append("id", id);

    await fetch(url, {
      method: "POST",
      headers: headers,
      body: form_data,
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
      "X-CSRFToken": token,
      "X-Requested-With": "XMLHttpRequest",
    };
    form_data = new FormData();
    form_data.append("action", action);
    form_data.append("id", id);
    await fetch(url, {
      method: "POST",
      headers: headers,
      body: form_data,
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
    if (document.querySelector(".form-help-inline")) {
      document
        .querySelector(".form-help-inline")
        .closest("div.form-group")
        .classList.remove("has-error");
      document.querySelector(".form-help-inline").remove();
    }

    if (verify_fields() && verify_end_start_items() && overlaptest()) {
      let form_enrich = document.querySelector("form#form_enrich");
      form_enrich.style.display = "none";
      var data_form = new FormData(form_enrich);

      let token = elt.querySelector("input[name=csrfmiddlewaretoken]").value;
      let url = window.location.href;
      let headers = {
        "X-CSRFToken": token,
        "X-Requested-With": "XMLHttpRequest",
      };
      data_form.append("action", action);

      await fetch(url, {
        method: "POST",
        headers: headers,
        body: data_form,
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
      "X-CSRFToken": token,
      "X-Requested-With": "XMLHttpRequest",
    };
    let form_data = new FormData();
    form_data.append("action", action);
    form_data.append("file", file);
    await fetch(url, {
      method: "POST",
      headers: headers,
      body: form_data,
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
  if (e.target.id != "id_type") return;
  enrich_type();
  let file_input = document.body.querySelector("#filewidget_script");
  if (file_input) {
    eval(file_input.innerHTML);
  }
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
  var form = document.getElementById("form_enrich");
  form.style.display = "none";
  //form.innerHTML = data;
  let htmlData = new DOMParser().parseFromString(data, "text/html").body
    .firstChild;
  form.innerHTML(htmlData);
  htmlData.querySelectorAll("script").forEach((item) => {
    if (item.src) {
      let script = document.createElement("script");
      script.src = item.src;
      document.body.appendChild(script);
    } else {
      // inline script
      (0, eval)(item.innerHTML);
    }
  });

  fadeIn(form);
  var inputStart = document.getElementById("id_start");
  inputStart.insertAdjacentHTML(
    "beforebegin",
    "&nbsp;<div class='getfromvideo pull-right mb-1'><a href='' id='getfromvideo_start' class='btn btn-primary btn-sm'>" +
      gettext("Get time from the player") +
      "</a><span class='timecode'></span></div>"
  );
  var inputStart = document.getElementById("id_end");
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
  document.getElementById("id_image").closest("div.form-group").style.display =
    "none";
  document
    .querySelector("textarea#id_richtext")
    .closest("div.form-group").style.display = "none";

  document
    .getElementById("id_weblink")
    .closest("div.form-group").style.display = "none";

  document
    .getElementById("id_document")
    .closest("div.form-group").style.display = "none";

  document.getElementById("id_embed").closest("div.form-group").style.display =
    "none";
  var val = document.querySelector("select#id_type").value;
  if (val != "") {
    var form = document.getElementById("form_enrich");
    form.querySelectorAll('[id^="id_' + val + '"]').forEach((elt) => {
      elt.closest("div.form-group").style.display = "block";
    });
  }
}
document.addEventListener("change", (e) => {
  if (e.target.id != "id_start") return;

  e.target.parentNode.querySelector(
    "span.getfromvideo span.timecode"
  ).innerHTML = " " + parseInt(e.target.value).tMoHHMSS();
});
document.addEventListener("change", (e) => {
  if (e.target.id != "id_end") return;
  e.target.parentNode.querySelector(
    "span.getfromvideo span.timecode"
  ).innerHTML = " " + parseInt(e.target.value).toHHMMSS();
});
document.addEventListener("click", (e) => {
  if (!e.target.matches("#page-video .getfromvideo a")) return;
  e.preventDefault();
  if (!(typeof player === "undefined")) {
    if (e.target.getAttribute("id") == "getfromvideo_start") {
      let inputStart = document.getElementById("id_start");
      inputStart.value = parseInt(player.currentTime());
      changeEvent = new Event("change");
      inputStart.dispatchEvent(changeEvent);
    } else {
      let inputEnd = document.getElementById("id_end");
      inputEnd.value = parseInt(player.currentTime());
      changeEvent = new Event("change");
      inputEnd.dispatchEvent(changeEvent);
    }
  }
});
/*** Verify if value of field respect form field ***/
function verify_fields() {
  var error = false;
  let inputTitle = document.getElementById("id_title");
  if (
    inputTitle.value == "" ||
    inputTitle.value.length < 2 ||
    inputTitle.value.length > 100
  ) {
    inputTitle.insertAdjacentHTML(
      "beforebegin",
      "<span class='form-help-inline'>&nbsp;&nbsp;" +
        gettext("Please enter a title from 2 to 100 characters.") +
        "</span>"
    );
    inputTitle.closest("div.form-group").classList.add("has-error");

    error = true;
  }
  let inputStart = document.getElementById("id_start");
  if (
    inputStart.value == "" ||
    inputStart.value < 0 ||
    inputStart.value >= video_duration
  ) {
    inputStart.insertAdjacentHTML(
      "beforebegin",
      "<span class='form-help-inline'>&nbsp; &nbsp;" +
        gettext("Please enter a correct start from 0 to ") +
        (video_duration - 1) +
        "</span>"
    );
    inputStart.closest("div.form-group").classList.add("has-error");

    error = true;
  }
  let inputEnd = document.getElementById("id_end");

  if (
    inputEnd.value == "" ||
    inputEnd.value <= 0 ||
    inputEnd.value > video_duration
  ) {
    inputEnd.insertAdjacentHTML(
      "beforebegin",
      "<span class='form-help-inline'>&nbsp; &nbsp;" +
        gettext("Please enter a correct end from 1 to ") +
        video_duration +
        "</span>"
    );
    inputEnd.closest("div.form-group").classList.add("has-error");

    error = true;
  }
  switch (document.getElementById("id_type").value) {
    case "image":
      let img = document.getElementById("id_image_thumbnail_img");
      if (img) {
        if (img.src == "/static/filer/icons/nofile_48x48.png") {
          //check with id_image value
          img.insertAdjacentElement(
            "beforebegin",
            "<span class='form-help-inline'>&nbsp; &nbsp;" +
              gettext("Please enter a correct image.") +
              "</span>"
          );
          img.closest("div.form-group").classList.add("has-error");
          error = true;
        }
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
        richtext.closest("div.form-group").classList.add("has-error");

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
        weblink.closest("div.form-group").classList.add("has-error");

        error = true;
      } else {
        if (weblink.value > 200) {
          weblink.insertAdjacentHTML(
            "beforebegin",
            "<span class='form-help-inline'>&nbsp; &nbsp;" +
              gettext("Weblink must be less than 200 characters.") +
              "</span>"
          );
          weblink.closest("div.form-group").classList.add("has-error");

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
        documentD.closest("div.form-group").classList.add("has-error");

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
        embed.closest("div.form-group").classList.add("has-error");

        error = true;
      } else {
        if (embed.value > 200) {
          embed.insertAdjacentHTML(
            "beforebegin",
            "<span class='form-help-inline'>&nbsp; &nbsp;" +
              gettext("Embed field must be less than 200 characters.") +
              "</span>"
          );

          embed.closes("div.form-group").classList.add("has-error");

          error = true;
        }
      }
      break;
    default:
      let inputType = document.getElementById("id_type");
      inputType.insertAdjacentHTML(
        "beforebegin",
        "<span class='form-help-inline'>&nbsp; &nbsp;" +
          gettext("Please enter a type in index field.") +
          "</span>"
      );
      inputType.closest("div.form-group").classList.add("has-error");

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
    var data_start = parseInt(e.dataset.start);
    var data_end = parseInt(e.dataset.end);
    if (
      id != e.dataset.id &&
      !(
        (new_start < data_start && new_end <= data_start) ||
        (new_start >= data_end && new_end > data_end)
      )
    ) {
      var text =
        gettext("There is an overlap with the enrichment ") +
        '"' +
        e.dataset.title +
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
