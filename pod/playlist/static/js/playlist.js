var showalert = (message, alerttype) => {
  document.body.append(
    `<div id="formalertdiv" class="alert ${alerttype} alert-dismissible fade show" role="alert">${message}<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button></div>`,
  );
  setTimeout(() => {
    document.getElementById("formalertdiv").remove();
  }, 5000);
};

var ajaxfail = function (data) {
  showalert(
    gettext("Error getting form.") +
      "(" +
      data +
      ")" +
      gettext("The form could not be recovered."),
    "alert-danger",
  );
};

document.addEventListener("DOMContentLoaded", function () {
  const table = document.getElementById("table_list_videos");

  Array.from(document.querySelectorAll(".position-up")).forEach((button) => {
    button.addEventListener("click", function () {
      let row = button.closest("tr");
      let currentposition = row.querySelector(".video-position");

      if (currentposition.textContent > 1) {
        let oldposition =
          row.previousElementSibling.querySelector(".video-position");
        currentposition.textContent = parseInt(currentposition.textContent) - 1;
        oldposition.textContent = parseInt(oldposition.textContent) + 1;
      }
      console.log(row.previousSibling);
      row.parentNode.insertBefore(row, row.previousElementSibling);
    });
  });

  document.querySelectorAll(".position-down").forEach((element) => {
    element.addEventListener("click", function () {
      let row = element.parentNode.parentNode;
      let currentposition = row.querySelector(".video-position");
      let oldposition = currentposition;
      if (row.nextElementSibling !== null) {
        oldposition = row.nextElementSibling.querySelector(".video-position");
      }

      if (parseInt(currentposition.textContent) < table.rows.length - 1) {
        currentposition.textContent = parseInt(currentposition.textContent) + 1;
        oldposition.textContent = parseInt(oldposition.textContent) - 1;
      }
      row.parentNode.insertBefore(row.nextElementSibling, row);
    });
  });
  let savePosition = document.getElementById("save-position");
  if (savePosition !== null) {
    savePosition.addEventListener("click", function () {
      var videos = {};
      for (let i = 1; i < table.rows.length; i++) {
        var slug = table.rows[i].children[1].attributes["data-slug"].value;
        var pos = table.rows[i].children[4].innerHTML;
        videos[slug] = pos;
      }
      let token = document.cookie
        .split(";")
        .filter((item) => item.trim().startsWith("csrftoken="))[0]
        .split("=")[1];

      form_data = new FormData();
      form_data.append("videos", JSON.stringify(videos));
      form_data.append("csrfmiddlewaretoken", token);
      form_data.append("action", "move");

      const return_url = $(this).data("return-url");
      var jqxhr = fetch(window.location.href, {
        method: "POST",
        headers: {
          "X-CSRFToken": token,
          "X-Requested-With": "XMLHttpRequest",
        },
        body: form_data,
      })
        .then((response) => {
          if (response.status !== 200) {
            showalert(
              gettext("You are no longer authenticated. Please log in again."),
              "alert-danger",
            );
          } else {
            showalert(gettext("Position saved"), "alert-success");
            window.location.reload();
          }
        })
        .catch((error) => {
          showalert(
            "Error moving videos. (" +
              error +
              ") The videos could not be moved.",
            "alert-danger",
          );
        });
    });
  }

  document.querySelectorAll(".position-delete").forEach((element) => {
    element.addEventListener("click", async function () {
      let slug = element.parentNode.parentNode
        .querySelector(".video-title")
        .getAttribute("data-slug");
      let token = document.cookie
        .split(";")
        .filter((item) => item.trim().startsWith("csrftoken="))[0]
        .split("=")[1];

      headers = {
        "X-CSRFToken": token,
        "X-Requested-With": "XMLHttpRequest",
      };

      form_data = new FormData();
      form_data.append("video", slug);
      form_data.append("action", "remove");

      await fetch(window.location.href, {
        method: "POST",
        headers: headers,
        body: form_data,
      })
        .then((response) => {
          if (response.status != 200) {
            showalert(
              gettext("You are no longer authenticated. Please log in again."),
              "alert-danger",
            );
          } else {
            response.json().then((data) => {
              if (data.success) {
                showalert(data.success, "alert-success");
                window.location.reload(); // hide link playlist
              } else {
                showalert(data.fail, "alert-danger");
              }
            });
          }
        })
        .catch((error) => {
          showalert(
            gettext(
              "Error deleting video from playlist. The video could not be deleted.",
            ),
            "alert-danger",
          );
        });
    });
  });

  document.querySelectorAll(".playlist-delete").forEach((element) => {
    const return_url = element.dataset.returnUrl;
    element.addEventListener("click", function () {
      let token = document.cookie
        .split(";")
        .filter((item) => item.trim().startsWith("csrftoken="))[0]
        .split("=")[1];
      if (confirm("Are you sure you want to delete this playlist?")) {
        headers = {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": token,
        };

        let form_data = new FormData();
        form_data.append("action", "delete");

        let jqxhr = fetch(window.location.href, {
          method: "POST",
          headers: headers,
          body: form_data,
        })
          .then((response) => {
            if (response.status != 200) {
              showalert(
                gettext(
                  "You are no longer authenticated. Please log in again.",
                ),
                "alert-danger",
              );
            } else {
              if (response.status == 200) {
                showalert(response.statusText, "alert-success");
                setTimeout(() => (window.location = return_url), 1000);
              } else {
                showalert(response.statusText, "alert-danger");
              }
            }
          })
          .catch((error) => {
            showalert(
              gettext(
                "Error deleting playlist. The playlist could not be deleted.",
              ),
              "alert-danger",
            );
          });
      }
    });
  });
  let infoVideo = document.getElementById("info-video");
  if (infoVideo !== null) {
    document
      .getElementById("info-video")
      .addEventListener("click", function (e) {
        let target = e.target;
        if (!target.classList.contains("playlist-item")) return;
        e.preventDefault();
        const url = window.location.href;
        const regex = new RegExp("(.*)/video/(\\d+-(.*))/");
        const checkslug = regex.test(url);
        const foundslug = url.match(regex);
        if (!checkslug) {
          showalert(
            gettext("The video can not be added from this page."),
            "alert-danger",
          );
          return;
        }
        if (!foundslug[2]) {
          showalert(gettext("The video slug not found."), "alert-danger");
          return;
        }

        const slug = target.getAttribute("data-slug");
        const link = target;
        let token = document.cookie
          .split(";")
          .filter((item) => item.trim().startsWith("csrftoken="))[0]
          .split("=")[1];

        form_data = new FormData();
        form_data.append("video", foundslug[2]);
        form_data.append("action", "add");

        const jqxhr = fetch("/playlist/edit/" + slug + "/", {
          method: "POST",
          headers: {
            "X-CSRFToken": token,
            "X-Requested-With": "XMLHttpRequest",
          },
          body: form_data,
        })
          .then((response) => {
            if (response.status == 200) {
              response.json().then((data) => {
                if (data.success) {
                  showalert(data.success, "alert-success");
                  //window.location.reload(); // hide link playlist
                  link.classList.add("disabled");
                  link.classList.remove("playlist-item");
                  link.append("");
                } else {
                  showalert(data.fail, "alert-danger");
                }
              });
            } else {
              showalert(
                gettext(
                  "You are no longer authenticated. Please log in again.",
                ),
                "alert-danger",
              );
            }
          })
          .catch((error) => {
            showalert(
              gettext(
                "Error getting video information. The video information could not be retrieved.",
              ),
              "alert-danger",
            );
          });
      });
  }
});
