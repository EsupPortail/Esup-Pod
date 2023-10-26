document.addEventListener("DOMContentLoaded", function () {
  let broadcastField = document.getElementById("event_broadcaster");
  let restrictedCheckBox = document.getElementById("event_is_restricted");
  let restrictedHelp = document.getElementById("event_is_restrictedHelp");
  let restrictedLabel = document.getElementsByClassName(
    "field_is_restricted",
  )[0];

  let change_restriction = (restrict) => {
    if (restrict === true) {
      restrictedCheckBox.checked = true;
      restrictedCheckBox.setAttribute("onclick", "return false");
      restrictedHelp.innerHTML = gettext(
        "Restricted because the broadcaster is restricted",
      );
      restrictedLabel.style.opacity = "0.5";
    } else {
      restrictedCheckBox.removeAttribute("onclick");
      restrictedHelp.innerHTML = gettext(
        "If this box is checked, the event will only be accessible to authenticated users.",
      );
      restrictedLabel.style.opacity = "";
    }
  };

  let getBroadcasterRestriction = () => {
    let broadcaster_id = broadcastField.value;

    if (
      typeof broadcaster_id === "undefined" ||
      broadcaster_id === "" ||
      isNaN(broadcaster_id)
    )
      return;

    let url =
      "/live/ajax_calls/getbroadcasterrestriction/?idbroadcaster=" +
      broadcaster_id;

    fetch(url, {
      method: "GET",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then((response) => {
        if (response.ok) return response.json();
        else return Promise.reject(response);
      })
      .then((s) => {
        change_restriction(s.restricted);
      })
      .catch((error) => {
        change_restriction(false);
        alert(gettext("An error occurred on broadcaster fetch..."));
      });
  };

  // Update broadcasters list after building change
  document
    .getElementById("event_building")
    .addEventListener("change", function () {
      let url =
        "/live/ajax_calls/getbroadcastersfrombuiding/?building=" + this.value;

      fetch(url, {
        method: "GET",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
      })
        .then((response) => {
          if (response.ok) return response.json();
          else return Promise.reject(response);
        })
        .then((broadcasters) => {
          broadcastField.innerHTML = "";

          if (Object.entries(broadcasters).length === 0) {
            broadcastField.disabled = true;
            broadcastField.innerHTML +=
              "<option value> " +
              gettext("No broadcaster set for this building") +
              "</option>";
          } else {
            broadcastField.disabled = false;
            for (const [key, value] of Object.entries(broadcasters)) {
              broadcastField.innerHTML +=
                '<option value="' + value.id + '">' + value.name + "</option>";
            }

            // Update restriction after list reload
            getBroadcasterRestriction();
          }
        })
        .catch((error) => {
          alert(gettext("An error occurred during broadcasters loading..."));
        });
    });

  // Update restriction after broadcaster change
  broadcastField.addEventListener("change", () => {
    getBroadcasterRestriction();
  });

  // Set restriction on load (if needed)
  getBroadcasterRestriction();
});
