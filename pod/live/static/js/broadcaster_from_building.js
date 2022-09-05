$(document).ready(function () {
  let broadcastField = $("#event_broadcaster");
  let restrictedCheckBox = $("#event_is_restricted");
  let restrictedHelp = $("#event_is_restrictedHelp");
  let restrictedLabel = $(".field_is_restricted");

  let change_restriction = (restrict) => {
    if (restrict === true) {
      restrictedCheckBox.prop("checked", true);
      restrictedCheckBox.attr("onclick", "return false");
      restrictedHelp.html(
        gettext("Restricted because the broadcaster is restricted")
      );
      restrictedLabel.css("opacity", "0.5");
    } else {
      restrictedCheckBox.removeAttr("onclick");
      restrictedHelp.html(
        gettext(
          "If this box is checked, the event will only be accessible to authenticated users."
        )
      );
      restrictedLabel.css("opacity", "");
    }
  };

  let getBroadcasterRestriction = () => {
    let broadcaster_id = broadcastField.find(":selected").val();
    if (typeof broadcaster_id === "undefined" || broadcaster_id === "") return;

    $.ajax({
      url: "/live/ajax_calls/getbroadcasterrestriction/",
      type: "GET",
      dataType: "JSON",
      cache: false,
      data: {
        idbroadcaster: broadcaster_id,
      },
      success: (s) => {
        change_restriction(s.restricted);
      },
      error: () => {
        change_restriction(false);
        alert(gettext("An error occurred on broadcaster fetch..."));
      },
    });
  };

  // Update broadcasters list after building change
  $("#event_building").change(function () {
    $.ajax({
      url: "/live/ajax_calls/getbroadcastersfrombuiding/",
      type: "GET",
      dataType: "JSON",
      cache: false,
      data: {
        building: this.value,
      },

      success: (broadcasters) => {
        broadcastField.html("");

        if (broadcasters.length === 0) {
          console.log("no Broadcaster");
          broadcastField.prop("disabled", true);
          broadcastField.append(
            "<option value> " +
              gettext("No broadcaster set for this building") +
              "</option>"
          );
        } else {
          broadcastField.prop("disabled", false);
          $.each(broadcasters, (key, value) => {
            broadcastField.append(
              '<option value="' + value.id + '">' + value.name + "</option>"
            );
          });

          // Update restriction after list reload
          getBroadcasterRestriction();
        }
      },
      error: () => {
        alert(gettext("An error occurred during broadcasters load..."));
      },
    });
  });

  // Update restriction after broadcaster change
  broadcastField.change(function () {
    getBroadcasterRestriction();
  });

  // Set restriction on load (if needed)
  getBroadcasterRestriction();
});
