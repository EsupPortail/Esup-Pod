var id_form = "form_chapter";
function show_form(data) {
  let form_chapter = document.getElementById(id_form);
  form_chapter.style.display = "none";
  form_chapter.innerHTML = data;
  form_chapter.querySelectorAll("script").forEach((item) => {
    if (item.src) {
      // external script

      let script = document.createElement("script");
      script.src = item.src;
      if (script.src.includes("filewidget.js"))
        document.body.appendChild(script);
    } else {
      // inline script
      if (item.id == "filewidget_script") (0, eval)(item.innerHTML);
    }
  });
  fadeIn(form_chapter);

  let inputStart = document.getElementById("id_time_start");
  if (inputStart) {
    inputStart.insertAdjacentHTML(
      "beforebegin",
      "&nbsp;<span class='getfromvideo'><a id='getfromvideo_start' class='btn btn-primary btn-sm'>" +
        gettext("Get time from the player") +
        "</a><span class='timecode'>&nbsp;</span></span>"
    );
  }
  let inputEnd = document.getElementById("id_time_end");
  if (inputEnd) {
    inputEnd.insertAdjacentHTML(
      "beforebegin",
      "&nbsp;<span class='getfromvideo'><a id='getfromvideo_end' class='btn btn-primary btn-sm'>" +
        gettext("Get time from the player") +
        "</a><span class='timecode'>&nbsp;</span></span>"
    );
  }
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
  document.querySelector("form.get_form").style;
  show_form("");
};

document.addEventListener("click", (e) => {
  if (e.target.id != "cancel_chapter") return;

  document.querySelectorAll("form.get_form").forEach((form) => {
    form.style.display = "block";
  });
  show_form("");
  let file_modal = document.getElementById("fileModal_id_file");
  if (file_modal) file_modal.remove();
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
  //document.querySelector("form.get_form").style.display = "none";
  let token = elt.querySelector("input[name=csrfmiddlewaretoken]").value;
  if (action == "new") {
    url = window.location.href;
    headers = {
      "X-CSRFToken": token,
      "X-Requested-With": "XMLHttpRequest",
    };
    form_data = new FormData();
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
        if (data.indexOf("list_chapter") == -1) {
          showalert(
            gettext("You are no longer authenticated. Please log in again."),
            "alert-danger"
          );
        } else {
          data = JSON.parse(data);
          updateDom(data);
          manageDelete();

          document.getElementById("list_chapter").innerHTML = data.list_chapter;
          show_form("");
          document.querySelector("form.get_form").style.display = "block";
        }
      })
      .catch((error) => {
        ajaxfail(error);
      });
  }
};

var sendform = async function (elt, action) {
  if (action == "save") {
    if (verify_start_title_items()) {
      let form_chapter = document.getElementById("form_chapter");
      form_chapter.style.display = "none";
      var data_form = new FormData(form_chapter);

      let token = elt.querySelector("input[name=csrfmiddlewaretoken]").value;
      let url = window.location.href;
      let headers = {
        "X-CSRFToken": token,
        "X-Requested-With": "XMLHttpRequest",
      };
      await fetch(url, {
        method: "POST",
        headers: headers,
        body: data_form,
        dataType: "html",
      })
        .then((response) => response.text())

        .then((data) => {
          if (
            data.indexOf("list_chapter") == -1 &&
            data.indexOf("form") == -1
          ) {
            showalert(
              gettext("You are no longer authenticated. Please log in again."),
              "alert-danger"
            );
          } else {
            data = JSON.parse(data);
            if (data.errors) {
              document.getElementById("form_chapter").style.display =
                "block";
              showalert(
                data.errors +
                  " Make sure your chapter start time is not 0 or equal to another chapter start time.",
                "alert-danger"
              );
            } else {
              updateDom(data);
              manageSave();
              document.getElementById("list_chapter").innerHTML =
                data.list_chapter;
              show_form("");
              document.querySelector("form.get_form").style.display = "block";
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

    form_data = new FormData();
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
        if (data.indexOf("list_chapter") == -1 && data.indexOf("form") == -1) {
          showalert(
            gettext("You are no longer authenticated. Please log in again."),
            "alert-danger"
          );
        } else {
          data = JSON.parse(data);

          if (data.errors) {
            document.getElementById("form_chapter").style.display = "block";
            showalert(
              data.errors +
                " Make sure you added a file and that it is a valid file.",
              "alert-danger"
            );
          } else {
            updateDom(data);
            manageImport();
            document.getElementById("list_chapter").innerHTML =
              data.list_chapter;
            show_form("");
            document.querySelector("form.get_form").style.display = "block";
          }
        }
      })
      .catch((error) => {
        ajaxfail(error);
      });
  }
};

/*** Verify if value of field respect form field ***/
function verify_start_title_items() {
  let inputTitle = document.getElementById("id_title");

  if (
    inputTitle.value == "" ||
    inputTitle.value.length < 2 ||
    inputTitle.value.length > 100
  ) {
    inputTitle.insertAdjacentElement(
      "beforebegin",
      "<span class='form-help-inline'>&nbsp;&nbsp;" +
        gettext("Please enter a title from 2 to 100 characters.") +
        "</span>"
    );
    inputTitle.parentNode.parentNode
      .querySelectorAll("div.form-group")
      .forEach(function (elt) {
        elt.classList.add("has-error");
      });

    return false;
  }
  let inputStart = document.getElementById("id_time_start");
  if (
    inputStart.value == "" ||
    inputStart.value < 0 ||
    inputStart.value >= video_duration
  ) {
    
    inputStart.insertAdjacentHTML(
      "beforebegin",
      "<span class='form-help-inline'>&nbsp;&nbsp;" +
        gettext("Please enter a correct start field between 0 and") +
        " " +
        (video_duration - 1) +
        "</span>"
    );
    inputStart.parentNode.parentNode
      .querySelectorAll("div.form-group")
      .forEach(function (elt) {
        elt.classList.add("has-error");
      });
    return false;
  }
  return true;
}

function overlaptest() {
  var new_start = parseInt(document.getElementById("id_time_start").value);
  var id = parseInt(document.getElementById("id_chapter").value);
  var msg = "";
  document.querySelectorAll("ul#chapters li").foreach(function (li) {
    if (
      id != li.getAttribute("data-id") &&
      new_start == lit.getAttribute("data-start")
    ) {
      var text =
        gettext("The chapter") +
        ' "' +
        li.getAttribute("data-title") +
        '" ' +
        gettext("starts at the same time.");
      msg += "<br/>" + text;
    }
  });
  return msg;
}

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

document.addEventListener("change", (event) => {
  if (!event.target.matches("#id_time_start")) return;
  event.target.parentNode
    .querySelectorAll("span.getfromvideo span.timecode")
    .forEach(function (span) {
      span.innerHTML = " " + parseInt(event.target.value).toHHMMSS();
    });
});
document.addEventListener("change", (event) => {
  if (!event.target.matches("#id_time_end")) return;
  event.target.parentNode
    .querySelectorAll("span.getfromvideo span.timecode")
    .forEach(function (span) {
      span.innerHTML = " " + parseInt(event.target.value).toHHMMSS();
    });
});

document.addEventListener("click", (event) => {
  if (!(typeof player === "undefined")) {
    if (event.target.matches("#getfromvideo_start")) {
      document.getElementById("id_time_start").value = Math.floor(
        player.currentTime()
      );
      const event = new Event("change");
      const time_start = document.getElementById("id_time_start");
      time_start.dispatchEvent(event);
    }
  }
});

var updateDom = function (data) {
  let player = window.videojs.players.podvideoplayer;
  let n1 = document.getElementById("chapters");
  let n2 = document.querySelector("div.chapters-list");
  let tmp_node = document.createElement("div");
  tmp_node.innerHTML = data["video-elem"];
  let chaplist = tmp_node.querySelector("div.chapters-list");
  if (n1 != null) {
    n1.parentNode.removeChild(n1);
  }
  if (n2 != null) {
    n2.parentNode.removeChild(n2);
  }
  if (chaplist != null && n2 != null) {
    chaplist.className = n2.className;
  }

  document
    .getElementById(window.videojs.players.podvideoplayer.id_)
    .append(chaplist);
  document
    .getElementById(window.videojs.players.podvideoplayer.id_)
    .append(tmp_node.querySelector("ul#chapters"));
};

var manageSave = function () {
  let player = window.videojs.players.podvideoplayer;
  if (player.usingPlugin("videoJsChapters")) {
    player.main();
  } else {
    player.videoJsChapters();
  }
};

var manageDelete = function () {
  let player = window.videojs.players.podvideoplayer;
  let n = document.querySelector("div.chapters-list");
  if (n != null) {
    player.main();
  } else {
    player.controlBar.chapters.dispose();
    player.videoJsChapters().dispose();
  }
};

var manageImport = function () {
  let player = window.videojs.players.podvideoplayer;
  let n = document.querySelector("div.chapters-list");
  if (n != null) {
    if (player.usingPlugin("videoJsChapters")) {
      player.main();
    } else {
      player.videoJsChapters();
    }
  } else {
    if (typeof player.controlBar.chapters != "undefined") {
      player.controlBar.chapters.dispose();
    }
    if (player.usingPlugin("videoJsChapters")) {
      player.videoJsChapters().dispose();
    }
  }
};
