document.addEventListener("DOMContentLoaded", function () {
  let broadcastField = document.getElementById("event_broadcaster");
  let restrictedCheckBox = document.getElementById("event_is_restricted");
  let restrictedHelp = document.getElementById("event_is_restrictedHelp");
  let restrictedLabel = document.querySelector(".field_is_restricted");

  let change_restriction = (restrict) => {
    if (restrict === true) {
      restrictedCheckBox.checked = true;
      restrictedCheckBox.setAttribute("onclick", "return false");
      restrictedHelp.innerHTML = gettext(
        "Restricted because the broadcaster is restricted"
      );
      restrictedLabel.style.opacity = "0.5";
    } else {
      restrictedCheckBox.removeAttribute("onclick");
      restrictedHelp.innerHTML = gettext(
        "If this box is checked, the event will only be accessible to authenticated users."
      );
      restrictedLabel.style.opacity = "1";
    }
  };

  let getBroadcasterRestriction = async () => {
    let select = broadcastField.querySelector("select");
    let broadcaster_id = select.options[select.selectedIndex].value;
    if (typeof broadcaster_id === "undefined" || broadcaster_id === "") return;

    let url = "/live/ajax_calls/getbroadcasterrestriction/";

    await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      cache: false,
      body: JSON.stringify({
        idbroadcaster: broadcaster_id,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        change_restriction(data.restricted);
      })
      .catch((error) => {
        change_restriction(false);
        alert(gettext("An error occurred on broadcaster fetch..."));
      });
  };

  // Update broadcasters list after building change
  document
    .getElementById("event_building")
    .addEventListener("change", async function () {
      let url = "/live/ajax_calls/getbroadcastersfrombuiding/";
      await fetch(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        cache: false,
        body: JSON.stringify({
          building: this.value,
        }),
      })
        .then((response) => response.json())
        .then((broadcasters) => {
          broadcastField.innerHTML = "";
          if (broadcasters.length === 0) {
            console.log("no Broadcaster");
            broadcastField.prop.disabled = true;
            broadcastField.append(
              "<option value> " +
                gettext("No broadcaster set for this building") +
                "</option>"
            );
          } else {
            broadcastField.prop.disabled = false;
            for (let i = 0; i < broadcasters.length; i++) {
              broadcastField.append(
                "<option value=" +
                  broadcasters[i].id +
                  ">" +
                  broadcasters[i].name +
                  "</option>"
              );
            }
            getBroadcasterRestriction();
          }
        })
        .catch((error) => {
          alert(gettext("An error occurred during broadcasters load..."));
        });
    });

  // Update restriction after broadcaster change
  broadcastField.change(function () {
    getBroadcasterRestriction();
  });

  // Set restriction on load (if needed)
  getBroadcasterRestriction();
});
