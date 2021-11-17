var showalert = function (message, alerttype) {
  $("body").append(
    '<div id="formalertdiv" class="alert ' +
      alerttype +
      ' alert-dismissible fade show" role="alert">' +
      message +
      '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button></div>'
  );
  setTimeout(function () {
    $("#formalertdiv").remove();
  }, 5000);
};

var ajaxfail = function (data) {
  showalert(
    "Error getting form. (" + data + ") The form could not be recovered.",
    "alert-danger"
  );
};

$(window).ready(function () {
  const table = $("#table_list_videos")[0];

  $(".position-up").on("click", function () {
    var row = $(this).parents("tr:first");
    var currentposition = row.find(".video-position");
    var oldposition = row.prev().find(".video-position");
    if (currentposition.text() > 1) {
      currentposition.text(parseInt(currentposition.text()) - 1);
      oldposition.text(parseInt(oldposition.text()) + 1);
    }
    row.insertBefore(row.prev());
  });

  $(".position-down").on("click", function () {
    var row = $(this).parents("tr:first");
    var currentposition = row.find(".video-position");
    var oldposition = row.next().find(".video-position");
    if (parseInt(currentposition.text()) < table.rows.length - 1) {
      currentposition.text(parseInt(currentposition.text()) + 1);
      oldposition.text(parseInt(oldposition.text()) - 1);
    }
    row.insertAfter(row.next());
  });

  $("#save-position").on("click", function () {
    var videos = {};
    for (let i = 1; i < table.rows.length; i++) {
      var slug = table.rows[i].children[1].attributes["data-slug"].value;
      var pos = table.rows[i].children[4].innerHTML;
      videos[slug] = pos;
    }
    data = JSON.stringify(videos);
    var jqxhr = $.ajax({
      method: "POST",
      url: window.location.href,
      data: {
        action: "move",
        videos: data,
        csrfmiddlewaretoken: $("#playlist_form")
          .find('input[name="csrfmiddlewaretoken"]')
          .val(),
      },
      dataType: "html",
    });
    jqxhr.done(function (data) {
      response = JSON.parse(data);
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
    });
    jqxhr.fail(function ($xhr) {
      var data = $xhr.status + " : " + $xhr.statusText;
      ajaxfail(data);
    });
  });

  $(".position-delete").on("click", function () {
    var slug = $(this)
      .parents("tr:first")
      .find(".video-title")
      .attr("data-slug");
    var jqxhr = $.ajax({
      method: "POST",
      url: window.location.href,
      data: {
        action: "remove",
        video: slug,
        csrfmiddlewaretoken: $("#playlist_form")
          .find('input[name="csrfmiddlewaretoken"]')
          .val(),
      },
      dataType: "html",
    });
    jqxhr.done(function (data) {
      response = JSON.parse(data);
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
    });
    jqxhr.fail(function ($xhr) {
      var data = $xhr.status + " : " + $xhr.statusText;
      ajaxfail(data);
    });
  });

  $(".playlist-delete").on("click", function () {
    if (confirm("Do you want to delete this playlist ?")) {
      var jqxhr = $.ajax({
        method: "POST",
        url: window.location.href,
        data: {
          action: "delete",
          csrfmiddlewaretoken: $(this)
            .parents("div:first")
            .find('input[name="csrfmiddlewaretoken"]')
            .val(),
        },
        dataType: "html",
      });
      jqxhr.done(function (data) {
        response = JSON.parse(data);
        if (!response.success && !response.fail) {
          showalert(
            "You are no longer authenticated. Please log in again.",
            "alert-danger"
          );
        } else {
          if (response.success) {
            showalert(response.success, "alert-success");
            window.location = "/my_playlists/";
          } else {
            showalert(response.fail, "alert-danger");
          }
        }
      });
      jqxhr.fail(function ($xhr) {
        var data = $xhr.status + " : " + $xhr.statusText;
        ajaxfail(data);
      });
    }
  });

  $("#info-video").on("click", ".playlist-item", function () {
    const vmslug = window.location.href.match(/video\/(\d{4}\-[^/?]*)/);
    if (!vmslug) {
      showalert(
        gettext("The video can not be added from this page."),
        "alert-danger"
      );
      return;
    }
    const slug = $(this).attr("data-slug"),
      jqxhr = $.ajax({
        method: "POST",
        url: "/playlist/edit/" + slug + "/",
        data: {
          action: "add",
          video: vmslug[1],
          csrfmiddlewaretoken: $(this)
            .parents(".dropdown-menu")
            .find("input")
            .val(),
        },
        dataType: "html",
      });
    jqxhr.done(function (data) {
      response = JSON.parse(data);
      console.log(response.success);
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
    });
    jqxhr.fail(function ($xhr) {
      var data = $xhr.status + " : " + $xhr.statusText;
      ajaxfail(data);
    });
  });
});
