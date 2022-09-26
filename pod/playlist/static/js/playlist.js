var showalert = (message, alerttype) => {
  document.body.append(
    `<div id="formalertdiv" class="alert ${alerttype} alert-dismissible fade show" role="alert">${message}<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button></div>`
  );
  setTimeout(() => {
    document.getElementById("formalertdiv").remove();
  }, 5000);
};

var ajaxfail = function (data) {
  showalert(
    "Error getting form. (" + data + ") The form could not be recovered.",
    "alert-danger"
  );
};

document.addEventListener("DOMContentLoaded", function () {
  const table = document.getElementById("table_list_videos");

  Array.from(document.querySelectorAll(".position-up")).forEach((element) => {
    let row = element.parentNode.parentNode;

    let currentposition = row.querySelectorAll(".video-position")[0];

    if (row.previousElementSibling !== null) {
      let oldposition =
        row.previousElementSibling.querySelectorAll(".video-position")[0];
    }
    let oldposition = currentposition;

    if (currentposition.textContent > 1) {
      currentposition.textContent = parseInt(currentposition.textContent) - 1;
      oldposition.textContent = parseInt(oldposition.textContent) + 1;
    }
    row.parentNode.insertBefore(row, row.previousSibling);
  });

  document.querySelectorAll(".position-down").forEach((element) => {
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
    row.parentNode.insertBefore(row.nextSibling, row);
  });

  document
    .getElementById("save-position")
    .addEventListener("click", function () {
      var videos = {};
      for (let i = 1; i < table.rows.length; i++) {
        var slug = table.rows[i].children[1].attributes["data-slug"].value;
        var pos = table.rows[i].children[4].innerHTML;
        videos[slug] = pos;
      }
      data = JSON.stringify(videos);

      var jqxhr = fetch(window.location.href, {
        method: "POST",
        body: {
          action: "move",
          videos: data,
          csrfmiddlewaretoken: document
            .getElementById("playlist_form")
            .querySelector('input[name="csrfmiddlewaretoken"]').value,
        },
      })
        .then((response) => {
          JSON.parse(response);
          if (!response.success && !response.fail) {
            showalert(
              "You are no longer authenticated. Please log in again.",
              "alert-danger"
            );
          } else {
            if (response.success) {
              showalert(response.success, "alert-success");
              window.location.reload();
            } else {
              showalert(response.fail, "alert-danger");
            }
          }
        })
        .catch((error) => {
          showalert(
            "Error moving videos. (" +
              error +
              ") The videos could not be moved.",
            "alert-danger"
          );
        });
    });

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
        "Content-Type": "application/json",
        "X-CSRFToken": token,
      };
      body = {
        video: slug,
        action: "remove",
        csrfmiddlewaretoken: token,
      };

      await fetch(window.location.href, {
        method: "POST",
        headers: headers,
        body: JSON.stringify(body),
      })
        .then((response) => {
          console.log(response.status);

          if (response.status != 200) {
            showalert(
              "You are no longer authenticated. Please log in again.",
              "alert-danger"
            );
          } else {
            showalert(response.statusText, "alert-success");
            //window.location.reload();
          }
        })
        .catch((error) => {
          showalert(
            "Error deleting video. (" +
              error +
              ") The video could not be deleted.",
            "alert-danger"
          );
        });
    });
  });

  document.querySelectorAll(".playlist-delete").forEach((element) => {
    element.addEventListener("click", function () {
      let token = document.cookie
        .split(";")
        .filter((item) => item.trim().startsWith("csrftoken="))[0]
        .split("=")[1];
      if (confirm("Are you sure you want to delete this playlist?")) {
        headers = {
          "X-CSRFToken": token,
        };
        let jqxhr = fetch(window.location.href, {
          method: "POST",
          headers: headers,
          body: {
            action: "delete",
            csrfmiddlewaretoken: token,
          },
        })
          .then((response) => {
            if (response.status != 200) {
              showalert(
                "You are no longer authenticated. Please log in again.",
                "alert-danger"
              );
            } else {
              if (response.status == 200) {
                showalert(response.statusText, "alert-success");
              } else {
                showalert(response.statusText, "alert-danger");
              }
            }
          })
          .catch((error) => {
            showalert(
              "Error deleting playlist. (" +
                error +
                ") The playlist could not be deleted.",
              "alert-danger"
            );
          });
      }
    });
  });
  /*
  document.getElementById("info-video").addEventListener("click", function (e) {
    e.preventDefault();
    const url = window.location.href;
    const regex = new RegExp("(.*)/video/(\\d+-(.*))/");
    const checkslug = regext.test(url);
    const foundslug = url.match(regex);
    if (!checkslug) {
      showalert(
        "Error getting video information.",
        "alert-danger",
        "alert-danger"
      );
      return;
    }
    if (!foundslug[2]) {
      showalert("The video slug not found.", "alert-danger", "alert-danger");
      return;
    }
    const slug = foundslug[2];
    const link = this.href;
    const jqxhr = fetch(window.location.href, {
      method: "POST",
      body: {
        action: "info",
        video: slug,
        csrfmiddlewaretoken:
          document.getElementById("playlist_form").children[0].value,
      },
    })
      .then((response) => {
        JSON.parse(response);
        if (!response.success && !response.fail) {
          showalert(
            "You are no longer authenticated. Please log in again.",
            "alert-danger",
            "alert-danger"
          );
        } else {
          if (response.success) {
            showalert(response.success, "alert-success", "alert-success");
            link.classList.add("disabled");
            link.classList.remove("playlist-item");
            link.append("");
          } else {
            showalert(response.fail, "alert-danger", "alert-danger");
          }
        }
      })
      .catch((error) => {
        showalert(
          "Error getting video information. (" +
            error +
            ") The video information could not be retrieved.",
          "alert-danger",
          "alert-danger"
        );
      });
  });
  */
});
