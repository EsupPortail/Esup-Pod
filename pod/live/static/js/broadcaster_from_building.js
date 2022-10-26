document.addEventListener("DOMContentLoaded", function () {
  var broadcastField = document.getElementById("event_broadcaster");
  var restrictedCheckBox = document.getElementById("event_is_restricted");
  var restrictedHelp = document.getElementById("event_is_restrictedHelp");
  var restrictedLabel = document.querySelector(".field_is_restricted");

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
    let select = broadcastField
    let broadcaster_id = select.options[select.selectedIndex].value;
    if (typeof broadcaster_id === "undefined" || broadcaster_id === "") return;

    let url = "/live/ajax_calls/getbroadcasterrestriction/?idbroadcaster=" + broadcaster_id;
    await fetch(url, {
      method: "GET",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
      
    })
      .then((response) => response.json())
      .then((data) => {
        change_restriction(data.restricted);
      })
      .catch((error) => {
        console.log(error)
        change_restriction(false);
        alert(gettext("An error occurred on broadcaster fetch..."));
      });
  };

  // Update broadcasters list after building change
  document
    .getElementById("event_building")
    .addEventListener("change", async function () {
      let url = "/live/ajax_calls/getbroadcastersfrombuiding/?building=" + this.value;    
      await fetch(url, {
        method: "GET",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
        },
        cache: false,
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
  broadcastField.addEventListener("change", function () {
    getBroadcasterRestriction();
  });

  // Set restriction on load (if needed)
  getBroadcasterRestriction();
});
