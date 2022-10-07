/** FUNCTIONS **/
function getParents(el, parentSelector /* optional */) {
  // If no parentSelector defined will bubble up all the way to *document*
  if (parentSelector === undefined) {
    parentSelector = document;
  }

  var parents = [];
  var p = el.parentNode;

  while (p !== parentSelector) {
    var o = p;
    parents.push(o);
    p = o.parentNode;
  }
  parents.push(parentSelector); // Push that parentSelector you wanted to stop at

  return parents;
}

function slideUp(target, duration = 500, callback = null) {
  target.style.transitionProperty = "height, margin, padding";
  target.style.transitionDuration = duration + "ms";
  target.style.boxSizing = "border-box";
  target.style.height = target.offsetHeight + "px";
  target.offsetHeight;
  target.style.overflow = "hidden";
  target.style.height = 0;
  target.style.paddingTop = 0;
  target.style.paddingBottom = 0;
  target.style.marginTop = 0;
  target.style.marginBottom = 0;
  window.setTimeout(() => {
    target.style.display = "none";
    target.style.removeProperty("height");
    target.style.removeProperty("padding-top");
    target.style.removeProperty("padding-bottom");
    target.style.removeProperty("margin-top");
    target.style.removeProperty("margin-bottom");
    target.style.removeProperty("overflow");
    target.style.removeProperty("transition-duration");
    target.style.removeProperty("transition-property");
    callback();
    //alert("!");
  }, duration);
}

function fadeIn(el, display) {
  el.style.opacity = 0;
  el.style.display = display || "block";
  (function fade() {
    var val = parseFloat(el.style.opacity);
    if (!((val += 0.1) > 1)) {
      el.style.opacity = val;
      requestAnimationFrame(fade);
    }
  })();
}

function linkTo_UnCryptMailto(s) {
  location.href = "mailto:" + window.atob(s);
}

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

// Edit the iframe and share link code
function writeInFrame() {
  // Iframe
  var txtintegration = document.getElementById("txtintegration");
  var str = txtintegration.value;
  // Autoplay
  if (document.getElementById("autoplay").checked) {
    if (str.indexOf("autoplay=true") < 0) {
      str = str.replace("is_iframe=true", "is_iframe=true&autoplay=true");
    }
  } else if (str.indexOf("autoplay=true") > 0) {
    str = str.replace("&autoplay=true", "");
  }
  // Loop
  if (document.getElementById("loop").checked) {
    if (str.indexOf("loop=true") < 0) {
      str = str.replace("is_iframe=true", "is_iframe=true&loop=true");
    }
  } else if (str.indexOf("loop=true") > 0) {
    str = str.replace("&loop=true", "");
  }
  txtintegration.value = str;

  // Share link
  var link = document.getElementById("txtpartage").value;
  // Autoplay
  if (document.getElementById("autoplay").checked) {
    if (link.indexOf("autoplay=true") < 0) {
      if (link.indexOf("?") < 0) link = link + "?autoplay=true";
      else if (link.indexOf("loop=true") > 0 || link.indexOf("start=") > 0)
        link = link + "&autoplay=true";
      else link = link + "autoplay=true";
    }
  } else if (link.indexOf("autoplay=true") > 0) {
    link = link
      .replace("&autoplay=true", "")
      .replace("autoplay=true&", "")
      .replace("?autoplay=true", "?");
  }
  // Loop
  if (document.getElementById("loop").checked) {
    if (link.indexOf("loop=true") < 0) {
      if (link.indexOf("?") < 0) link = link + "?loop=true";
      else if (link.indexOf("autoplay=true") > 0 || link.indexOf("start=") > 0)
        link = link + "&loop=true";
      else link = link + "loop=true";
    }
  } else if (link.indexOf("loop=true") > 0) {
    link = link
      .replace("&loop=true", "")
      .replace("?loop=true&", "?")
      .replace("?loop=true", "?");
  }

  //Remove ? to start when he's first
  if (link.indexOf("??") > 0) link = link.replace(/\?\?/, "?");

  document.getElementById("txtpartage").value = link;

  var img = document.getElementById("qrcode");
  var imgsrc = "//chart.apis.google.com/chart?cht=qr&chs=200x200&chl=" + link;
  if (img.getAttribute("src") === "") img.setAttribute("data-src", imgsrc);
  else img.src = imgsrc;
}
document.addEventListener("change", (e) => {
  if (e.target.id === "autoplay" || e.target.id === "loop") writeInFrame();
});

document.addEventListener("shown.bs.collapse", (e) => {
  if (e.target.id === "qrcode")
    e.target.setAttribute("src", e.target.getAttribute("data-src"));
});

document.addEventListener("hidden.bs.collapse", (e) => {
  if (e.target.id === "qrcode") e.target.setAttribute("src", "");
});

document.addEventListener("change", (e) => {
  if (e.target.id !== "displaytime") return;
  let displayTime = document.getElementById("displaytime");
  let txtpartage = document.getElementById("txtpartage");
  if (displayTime.checked) {
    if (txtpartage.value.indexOf("start") < 0) {
      txtpartage.value =
        txtpartage.value + "&start=" + parseInt(player.currentTime());

      if (txtpartage.value.indexOf("??") > 0)
        txtpartage.value = txtpartage.value.replace("??", "?");
      var valeur = txtpartage.value;
      txtpartage.value = valeur.replace(
        "/?",
        "/?start=" + parseInt(player.currentTime()) + "&"
      );
    }
    document.getElementById("txtposition").value = player
      .currentTime()
      .toHHMMSS();
  } else {
    txtpartage.value = txtpartage.value
      .replace(/(\&start=)\d+/, "")
      .replace(/(\start=)\d+/, "")
      .replace(/(\?start=)\d+/, "");

    txtpartage.valuex;
    document.getElementById("txtintegration").value.replace(/(start=)\d+&/, "");
    document.getElementById("txtposition").value = "";
  }

  //Replace /& => /?
  var link = txtpartage.value;
  if (link.indexOf("/&") > 0) link = link.replace("/&", "/?");
  txtpartage.value = link;

  var img = document.getElementById("qrcode");
  img.src =
    "//chart.apis.google.com/chart?cht=qr&chs=200x200&chl=" + txtpartage.value;
});

/*** USE TO SHOW THEME FROM CHANNELS ***/
var get_list = function (
  tab,
  level,
  tab_selected,
  tag_type,
  li_class,
  attrs,
  add_link,
  current,
  channel,
  show_only_parent_themes = false
) {
  level = level || 0;
  tab_selected = tab_selected || [];
  tag_type = tag_type || "option";
  li_class = li_class || "";
  attrs = attrs || "";
  add_link = add_link || false;
  current = current || false;
  channel = channel || "";
  var list = "";
  var prefix = "";
  for (i = 0; i < level; i++) prefix += "&nbsp;&nbsp;";
  if (level != 0) prefix += "|-";
  document.forEach(function (_, val) {
    var title = add_link
      ? '<a href="' + val.url + '">' + channel + " " + val.title + "</a>"
      : channel + " " + val.title;
    var selected =
      $.inArray(val.id.toString(), tab_selected) > -1 ? "selected" : "";
    var list_class = 'class="' + li_class;
    if (val.slug == current) list_class += ' list-group-item-info"';
    else list_class += '"';
    list +=
      "<" +
      tag_type +
      " " +
      selected +
      " " +
      list_class +
      " " +
      attrs +
      ' value="' +
      val.id +
      '" id="theme_' +
      val.id +
      '">' +
      prefix +
      " " +
      title +
      "</" +
      tag_type +
      ">";
    var child = val.child;
    var count = Object.keys(child).length;
    if (count > 0 && !show_only_parent_themes) {
      list += get_list(
        child,
        level + 1,
        tab_selected,
        tag_type,
        li_class,
        attrs,
        add_link,
        current,
        channel
      );
    }
  });
  return list;
};

/*** CHANNELS IN NAVBAR ***/

document.querySelectorAll(".collapsibleThemes").forEach((cl) => {
  cl.addEventListener("show.bs.collapse", function () {
    var str = get_list(
      listTheme["channel_" + cl.dataset.id],
      0,
      [],
      (tag_type = "li"),
      (li_class = "list-inline-item"),
      (attrs = ""),
      (add_link = true),
      (current = ""),
      (channel = ""),
      (show_only_parent_themes = show_only_parent_themes)
    );
    cl.innerHTML = '<ul class="list-inline p-1 border">' + str + "</ul>";
    //$(this).parents("li").addClass('list-group-item-light');
    cl.parentNode.querySelectorAll("li").forEach((li) =>
      li.querySelectorAll(".chevron-down").forEach((el) => {
        el.setAttribute("style", "transform: rotate(180deg);");
      })
    );
  });
});
document.querySelectorAll(".collapsibleThemes").forEach((cl) => {
  cl.addEventListener("hidden.bs.collapse", function () {
    // do something…
    //$(this).parents("li").removeClass('list-group-item-light');
    cl.parentNode.querySelectorAll("li").forEach((li) => {
      li.querySelectorAll(".chevron-down").forEach((el) => {
        el.setAttribute("style", "");
      });
    });
  });
});

let ownerboxnavbar = document.getElementById("ownerboxnavbar");
if (ownerboxnavbar) {
  ownerboxnavbar.addEventListener("keyup", function () {
    if (ownerboxnavbar.value && ownerboxnavbar.value.length > 2) {
      var searchTerm = ownerboxnavbar.value;
      url = "/ajax_calls/search_user?term=" + searchTerm;
      fetch(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      })
        .then((response) => response.json())
        .then((data) => {
          let accordion = document.getElementById("accordion");
          accordion.innerHTML = "";
          data.forEach((elt) => {
            accordion.append(
              '<li><a href="' +
                urlvideos +
                "?owner=" +
                elt.username +
                '">' +
                elt.first_name +
                " " +
                elt.last_name +
                (!HIDE_USERNAME
                  ? " (" + elt.username + ")</a></li>"
                  : "</a></li>")
            );
          });
        });
    } else {
      document.getElementById("#accordion").innerHTML = "";
    }
  });
}

/** COOKIE DIALOG **/

document.addEventListener("DOMContentLoaded", function () {
  let consent = Cookies.get("podCookieConsent");
  var cookieDiv = document.getElementById("cookieModal");
  var cookieModal = new bootstrap.Modal(cookieDiv);
  if (consent != null && consent == "ok") {
    cookieModal.hide();
  } else {
    cookieModal.show();
  }
  document.addEventListener("click", (e) => {
    if (e.target.id != "okcookie") return;
    let expiryDate = new Date();
    expiryDate.setFullYear(expiryDate.getFullYear() + 1);
    document.cookie =
      "podCookieConsent=ok; path=/; expires=" + expiryDate.toGMTString();
    cookieModal.hide();
  });
});
/** MENU ASIDE **/
document.addEventListener("DOMContentLoaded", function () {
  //.collapseAside is on the toggle button
  //#collapseAside is the side menu
  // Fired when #collapseAside has been made visible

  let collapseAside = document.getElementById("collapseAside");
  if (collapseAside != null) {
    let collapseBoot = new bootstrap.Collapse(collapseAside, {
      toggle: false,
    });

    collapseAside.addEventListener("shown.bs.collapse", function () {
      Cookies.set("activeCollapseAside", "open", { sameSite: "Lax" });

      // '<i class="bi bi-arrow-90deg-up"></i><i class="bi bi-list"></i>'
      let mainContent = document.getElementById("mainContent");
      if (mainContent) {
        document.getElementById("mainContent").classList.add("col-md-9");
      }
    });
    // Fired when #collapseAside has been hidden
    collapseAside.addEventListener("hidden.bs.collapse", function () {
      Cookies.set("activeCollapseAside", "close", { sameSite: "Lax" });

      // '<i class="bi bi-arrow-90deg-down"></i><i class="bi bi-list"></i>'

      document.getElementById("mainContent").classList.add("col-md-9");
    });

    // If aside menu is empty, hide container and button
    if (collapseAside.querySelectorAll("div").length == 0) {
      collapseAside.style.display = "none";
      collapseBoot.show();
      // Destroy collapse object
      collapseBoot.dispose();
      let mainContent = document.getElementById("mainContent");
      if (mainContent) {
        document.getElementById("mainContent").classList.remove("col-md-9");
      }
    } else {
      // Use the last aside state, stored in Cookies
      // only for > 992, we show collapseAside
      var last = Cookies.get("activeCollapseAside");
      if (last != null && last == "close") {
        collapseBoot.hide();
        document.querySelector(".collapseAside").innerHTML;
        // '<i class="bi bi-arrow-90deg-down"></i><i class="bi bi-list"></i>'
        // $("#mainContent").removeClass("col-md-9");
      } else {
        if (window.innerWidth > 992) {
          collapseBoot.show();
        }
      }
    }
    TriggerAlertClose();
  }
});

function TriggerAlertClose() {
  // Automatically hide success type alerts
  // (alert-warning and alert-danger will remain on screen)
  window.setTimeout(function () {
    document
      .querySelectorAll(".alert.alert-success, .alert.alert-info")
      .forEach((el) => {
        el.animate(
          {
            opacity: 0,
          },
          {
            duration: 1000,
          }
        );
        slideUp(el, 1000, function () {
          el.remove();
        });
      });
  }, 5000);
}
/*** FORM THEME USER PICTURE ***/
/** PICTURE **/
document.addEventListener("click", (e) => {
  if (!e.target.classList.contains("get_form_userpicture")) return;
  send_form_data(e.target.dataset.url, {}, "append_picture_form", "get");
});
document.addEventListener("hidden.bs.modal", (e) => {
  if (e.target.id != "userpictureModal") return;

  e.target.remove();
  document.getElementById("fileModal_id_userpicture").remove();
});
document.addEventListener("submit", (e) => {
  if (e.target.id != "userpicture_form") return;
  e.preventDefault();
  let form = e.target;
  let data_form = new FormData(form);
  send_form_data(
    e.target.getAttribute("action"),
    data_form,
    "show_picture_form"
  );
});
/** THEME **/
document.addEventListener("submit", (e) => {
  if (e.target.id != "form_theme") return;
  e.preventDefault();
  let form = e.target;
  let data_form = new FormData(form);
  send_form_data(form.getAttribute("action"), data_form, "show_theme_form");
});
document.addEventListener("click", (e) => {
  if (e.target != "cancel_theme") return;
  document.querySelector("form.get_form_theme").style.display = "block";
  show_form_theme("");
  document
    .getElementById("table_list_theme tr")
    .classList.remove("table-primary");
  window.scrollTo({
    top: parseInt(document.getElementById("list_theme").offset().top),
    behavior: "smooth",
  });
});
document.addEventListener("submit", (e) => {
  if (!e.target.classList.contains("get_form_theme")) return;
  e.preventDefault();
  var action = e.target.querySelector("input[name=action]").value; // new, modify and delete
  if (action == "delete") {
    var deleteConfirm = confirm(
      gettext("Are you sure you want to delete this element?")
    );
    let form = e.target;
    let data_form = new FormData(form);
    if (deleteConfirm) {
      send_form_data(
        window.location.href,
        data_form,
        "show_form_theme_" + action
      );
    }
  } else {
    send_form_data(
      window.location.href,
      data_form,
      "show_form_theme_" + action
    );
  }
});
/** VIDEO DEFAULT VERSION **/
document.addEventListener("change", (e) => {
  if (
    e.target !==
    document.querySelector(
      "#video_version_form input[type=radio][name=version]"
    )
  ) {
    return;
  }
  document.getElementById("video_version_form").submit();
});
document.addEventListener("submit", (e) => {
  if (e.target.id != "video_version_form") return;
  e.preventDefault();
  let form = e.target;
  let data_form = new FormData(form);
  send_form_data(form.getAttribute("action"), data_form, "result_video_form");
});
var result_video_form = function (data) {
  if (data.errors) {
    showalert(
      gettext("One or more errors have been found in the form."),
      "alert-danger"
    );
  } else {
    showalert(gettext("Changes have been saved."), "alert-info");
  }
};

/** FOLDER **/

/** AJAX **/
var send_form_data = async function (
  url,
  data_form,
  fct,
  method,
  callbackSuccess = undefined,
  callbackFail = undefined
) {
  callbackSuccess =
    typeof callbackSuccess === "function"
      ? callbackSuccess
      : function ($data) {
          return $data;
        };
  callbackFail =
    typeof callbackFail === "function" ? callbackFail : function ($xhr) {};

  method = method || "post";

  let token = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

  form_data = "";

  if (!(data_form instanceof FormData)) {
    form_data = new FormData();
    for (let key in data_form) {
      form_data.append(key, data_form[key]);
    }
  } else {
    form_data = data_form;
  }

  if (method == "post") {
    fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": token,
      },
      body: form_data,
    })
      .then((response) => response.text())
      .then(($data) => {
        $data = callbackSuccess($data);
        window[fct]($data);
      })

      .catch((error) => {
        showalert(
          gettext("Error during exchange") +
            "(" +
            error +
            ")<br/>" +
            gettext("No data could be stored."),
          "alert-danger"
        );
        callbackFail(error);
      });
  } else {
    await fetch(url, {
      method: "GET",
      
    })
      .then((response) => response.text())
      .then(($data) => {
        $data = callbackSuccess($data);
        window[fct]($data);
      })
    
      .catch((error) => {
        showalert(
          gettext("Error during exchange") +
            "(" +
            error +
            ")<br/>" +
            gettext("No data could be stored."),
          "alert-danger"
        );

        callbackFail(error);
      });
      
  }
};

var show_form_theme_new = function (data) {
  if (data.indexOf("form_theme") == -1) {
    showalert(
      gettext("You are no longer authenticated. Please log in again."),
      "alert-danger"
    );
  } else {
    show_form_theme(data);
  }
};
var show_form_theme_modify = function (data) {
  if (data.indexOf("theme") == -1) {
    showalert(
      gettext("You are no longer authenticated. Please log in again."),
      "alert-danger"
    );
  } else {
    show_form_theme(data);
    var id = data.querySelector("#id_theme").value;
    document.querySelector("#theme_" + id).classList.add("table-primary");
  }
};
var show_form_theme_delete = function (data) {
  if (data.list_element) {
    show_list_theme(data.list_element);
  } else {
    showalert(
      gettext("You are no longer authenticated. Please log in again."),
      "alert-danger"
    );
  }
};
var show_theme_form = function (data) {
  if (data.list_element || data.form) {
    if (data.errors) {
      showalert(
        gettext("One or more errors have been found in the form."),
        "alert-danger"
      );
      show_form_theme(data.form);
    } else {
      show_form_theme("");
      document.querySelector("form.get_form_theme").style.display = "block";
      show_list_theme(data.list_element);
    }
  } else {
    showalert(
      gettext("You are no longer authenticated. Please log in again."),
      "alert-danger"
    );
  }
};
var userpicture = document.getElementById("userpictureModal");
if (userpicture) {
  var userPictureModal = new bootstrap.Modal(userpicture, {
    keyboard: false,
  });
}

var show_picture_form = function (data) {
  document.getElementById("userpicture_form").innerHTML =
    data.querySelector("#userpicture_form").innerHTML;
  if (data.querySelector("#userpictureurl").value) {
    //$(".get_form_userpicture").html('<img src="'+$(data).find("#userpictureurl").val()+'" height="34" class="rounded" alt="" loading="lazy">Change your picture');
    document.querySelector("#nav-usermenu .userpicture").remove();
    document.querySelector("#nav-usermenu .userinitial").style.display = "none";
    document
      .querySelector("#nav-usermenu > button")
      .classList.remove("initials btn btn-primary");
    document.querySelector("#nav-usermenu > button").classList.add("nav-link");
    document
      .querySelector("#nav-usermenu > button")
      .append(
        '<img src="' +
          data.querySelector("#userpictureurl").value +
          '" class="userpicture rounded" alt="avatar" loading="lazy">'
      );
    //$(".get_form_userpicture").html($(".get_form_userpicture").children());
    document.querySelector(".get_form_userpicture").innerHTML =
      '<i class="bi bi-card-image pod-nav-link-icon d-lg-none d-xl-inline mx-1"></i>' +
      gettext("Change your picture");
  } else {
    document.querySelector("#nav-usermenu .userpicture").remove();
    document.querySelector("#nav-usermenu .userinitial").style.display =
      "inline-block";
    document
      .querySelector("#nav-usermenu > button")
      .classList.add("initials btn btn-primary");
    //$(".get_form_userpicture").html($(".get_form_userpicture").children());
    document.querySelector(".get_form_userpicture").innerHTML =
      '<i class="bi bi-card-image pod-nav-link-icon d-lg-none d-xl-inline mx-1"></i>' +
      gettext("Add your picture");
  }
  userpictureModal.hide();
};
var append_picture_form = function (data) {
  document.body.append(data);
  userpictureModal.show();
};
function show_form_theme(data) {
  let div_form = document.getElementById("div_form_theme");
  div_form.style.display = "none";
  div_form.innerHTML = data;
  fadeIn(div_form);
  if (data != "")
    document.querySelector("form.get_form_theme").style.display = "none";
  window.scrollTo({
    top: parseInt(document.getElementById("div_form_theme").offset().top),
    behavior: "smooth",
  });
}
function show_list_theme(data) {
  let list_theme = document.getElementById("list_theme");
  list_theme.style.display = "none";
  list_theme.innerHTML = data;
  fadeIn(list_theme);
  //$('form.get_form_theme').show();
  window.scrollTo({
    top: parseInt(document.getElementById("list_theme").offset().top),
    behavior: "smooth",
  });
}
/***** VIDEOS *****/

let ownerbox = document.getElementById("ownerbox");
if (ownerbox) {
  ownerbox.addEventListener("keyup", async function () {
    let thisE = e.target;
    if (thisE.value && thisE.value.length > 2) {
      var searchTerm = thisE.value;
      var url = "/ajax/search_user/" + searchTerm;
      var cache = false;

      await fetch(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        cache: cache,
      })
        .then((response) => response.text())
        .then((data) => {
          document
            .querySelectorAll("#collapseFilterOwner .added")
            .forEach((index) => {
              var c = index.querySelector("input");
              if (!c.checked) {
                index.remove();
              }
            });

          data.forEach((elt) => {
            if (
              listUserChecked.indexOf(elt.username) == -1 &&
              document.querySelector("#collapseFilterOwner #id" + elt.username)
                .length == 0
            ) {
              data = JSON.parse(data);
              let username = HIDE_USERNAME ? "" : " (" + elt.username + ")";
              var chekboxhtml =
                '<div class="form-check added"><input class="form-check-input" type="checkbox" name="owner" value="' +
                elt.username +
                '" id="id' +
                elt.username +
                '"><label class="form-check-label" for="id' +
                elt.username +
                '">' +
                elt.first_name +
                " " +
                elt.last_name +
                username +
                "</label></div>";
              document
                .getElementById("collapseFilterOwner")
                .append(chekboxhtml);
            }
          });
        });
    } else {
      document
        .querySelectorAll("#collapseFilterOwner .added")
        .forEach((index) => {
          var c = index.querySelector("input");
          if (!c.checked) {
            index.remove();
          }
        });
    }
  });
  /****** VIDEOS EDIT ******/
  /** channel **/
}
var tab_initial = new Array();

let select = document.querySelector("#id_theme select");
if (select) {
  select.options.forEach((option) => {
    if (option.selected) {
      tab_initial.push(option.value);
    }
  });

  select.options.forEach((option) => {
    option.remove();
  });
}
let id_channel = document.getElementById("id_channel");
if (id_channel) {
  id_channel.addEventListener("change", function () {
    /*
    $('#id_channel').on('select2:select', function (e) {
      alert('change 2');
    });
    */
    // use click instead of change due to select2 usage : https://github.com/theatlantic/django-select2-forms/blob/master/select2/static/select2/js/select2.js#L1502
    //$("#id_channel").on("click", function (e) {
    //alert('change 3');
    document.querySelector("#id_theme option").remove();
    var tab_channel_selected = this.value;
    var str = "";
    for (var id in tab_channel_selected) {
      var chan = document
        .querySelector(
          "#id_channel option[value=" + tab_channel_selected[id] + "]"
        )
        .text();
      str += get_list(
        listTheme["channel_" + tab_channel_selected[id]],
        0,
        [],
        (tag_type = "option"),
        (li_class = ""),
        (attrs = ""),
        (add_link = false),
        (current = ""),
        (channel = chan + ": ")
      );
    }
    document.getElementById("id_theme").append(str);
  });
}

document.querySelectorAll("#id_channel select").forEach((select) => {
  if (select) {
    select.options.forEach((option) => {
      if (option.selected) {
        var str = get_list(
          listTheme["channel_" + option.value],
          0,
          tab_initial,
          (tag_type = "option"),
          (li_class = ""),
          (attrs = ""),
          (add_link = false),
          (current = "")
        );
        document.getElementById("id_theme").append(str);
      }
    });
  }
});

/** end channel **/
/*** Copy to clipboard ***/

let btnpartageprive = document.getElementById("btnpartageprive");
if (btnpartageprive) {
  btnpartageprive.addEventListener("click", function () {
    var copyText = document.getElementById("txtpartageprive");
    copyText.select();
    document.execCommand("copy");
    showalert(gettext("text copied"), "alert-info");
  });
}
/** Restrict access **/
/** restrict access to group */
let id_is_restricted = document.getElementById("id_is_restricted");
if (id_is_restricted) {
  id_is_restricted.addEventListener("click", function () {
    restrict_access_to_groups();
  });
}
var restrict_access_to_groups = function () {
  if (document.getElementById("id_is_restricted").checked) {
    let id_restricted_to_groups = document.getElementById(
      "id_restrict_access_to_groups"
    );
    let div_restricted = id_restricted_to_groups.closest(
      "div.restricted_access"
    );
    div_restricted.style.display = "block";
  } else {
    document
      .querySelectorAll("#id_restrict_access_to_groups select")
      .forEach((select) => {
        select.options.forEach((option) => {
          if (option.selected) {
            option.selected = false;
          }
        });
      });
    let id_restricted_to_groups = document.getElementById(
      "id_restrict_access_to_groups"
    );
    let div_restricted = id_restricted_to_groups.closest(
      "div.restricted_access"
    );

    div_restricted.style.display = "none";
  }
};

let id_is_draft = document.getElementById("id_is_draft");
if (id_is_draft) {
  id_is_draft.addEventListener("click", function () {
    restricted_access();
  });
}

var restricted_access = function () {
  let restricted_access = document.querySelector(".restricted_access");
  if (restricted_access) {
    let is_draft = document.getElementById("id_is_draft");
    if (is_draft != null && is_draft.checked) {
      restricted_access.classList.add("hide");
      restricted_access.classList.remove("show");
      document.getElementById("id_password").value;

      document
        .querySelectorAll("#id_restrict_access_to_groups select")
        .forEach((select) => {
          select.options.forEach((option) => {
            if (option.selected) {
              option.selected = false;
            }
          });
        });

      document.getElementById("id_is_restricted").checked = false;
    } else {
      restricted_access.classList.add("show");
      restricted_access.classList.remove("hide");
    }
    restrict_access_to_groups();
  }
};
restricted_access();
//restrict_access_to_groups();

/** end restrict access **/
/*** VALID FORM ***/
(function () {
  "use strict";
  window.addEventListener(
    "load",
    function () {
      // Fetch all the forms we want to apply custom Bootstrap validation styles to
      var forms = document.getElementsByClassName("needs-validation");
      // Loop over them and prevent submission
      var validation = Array.prototype.filter.call(forms, function (form) {
        form.addEventListener(
          "submit",
          function (event) {
            if (form.checkValidity() === false) {
              window.scrollTo($(form).scrollTop(), 0);
              showalert(
                gettext("Errors appear in the form, please correct them"),
                "alert-danger"
              );
              event.preventDefault();
              event.stopPropagation();
            } else {
              if (form.dataset.morecheck) {
                window[form.dataset.morecheck](form, event);
              }
            }
            form.classList.add("was-validated");
          },
          false
        );
      });
    },
    false
  );
})();
/*** VIDEOCHECK FORM ***/
var videocheck = function (form, event) {
  var fileInput = document.getElementById("id_video");
  if (fileInput.get(0).files.length) {
    var fileSize = fileInput.get(0).files[0].size;
    var fileName = fileInput.get(0).files[0].name;
    var extension = fileName
      .substring(fileName.lastIndexOf(".") + 1)
      .toLowerCase();
    if (listext.indexOf(extension) !== -1) {
      if (fileSize > video_max_upload_size) {
        window.scrollTo(document.getElementById("video_form").scrollTop(), 0);
        showalert(
          gettext("The file size exceeds the maximum allowed value:") +
            " " +
            VIDEO_MAX_UPLOAD_SIZE +
            gettext(" GB."),
          "alert-danger"
        );
        event.preventDefault();
        event.stopPropagation();
      } else {
        document.querySelector("#video_form fieldset").style.display = "none";
        document.querySelector("#video_form button").style.display = "none";

        let js_process = document.getElementById("js-process");
        js_process.style.display = "block";
        window.scrollTo(js_process.scrollTop(), 0);
        if (!show_progress_bar(form)) {
          event.preventDefault();
          event.stopPropagation();
        }
      }
    } else {
      window.scrollTo(document.getElementById("video_form").scrollTop(), 0);
      showalert(
        gettext("The file extension not in the allowed extension:") +
          " " +
          listext +
          ".",
        "alert-danger"
      );
      event.preventDefault();
      event.stopPropagation();
    }
  }
};

/***** SHOW ALERT *****/
var showalert = function (message, alerttype) {
  let textHtml =
    '<div id="formalertdiv" class="alert ' +
    alerttype +
    ' alert-dismissible fade show"  role="alert">' +
    message +
    '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="' +
    gettext("Close") +
    '"></button></div>';

  let parsedHTML = new DOMParser().parseFromString(textHtml, "text/html").body
    .firstChild;

  document.body.appendChild(parsedHTML);
  setTimeout(function () {
    let formalertdiv = document.getElementById("formalertdiv");
    if (formalertdiv) {
      formalertdiv.remove();
    }
  }, 5000);
};

function show_messages(msgText, msgClass, loadUrl) {
  var $msgContainer = document.getElementById("#show_messages");
  var close_button = "";
  msgClass = typeof msgClass !== "undefined" ? msgClass : "warning";
  loadUrl = typeof loadUrl !== "undefined" ? loadUrl : false;

  if (!loadUrl) {
    close_button =
      '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button>';
  }

  let $msgBox = document.createElement("div");
  $msgBox.classList.add(
    "alert",
    "alert-" + msgClass,
    "alert-dismissable",
    "fade",
    "in"
  );
  $msgBox.setAttribute("role", "alert");
  $msgBox.innerHTML = close_button + msgText;

  $msgContainer.innerHTML = $msgBox.outerHTML;

  if (loadUrl) {
    $msgBox.delay(4000).fadeOut(function () {
      if (loadUrl) {
        window.location.reload();
      } else {
        window.location.assign(loadUrl);
      }
    });
    setTimeout(function () {
      fadeOutIn($msgBox);
      if (loadUrl) {
        window.location.reload();
      }
    }, 5000);
  } else if (msgClass === "info" || msgClass === "success") {
    setTimeout(function () {
      fadeOutIn($msgBox);
      $msgBox.remove();
    }, 3000);
  }
}

function fadeOutIn(elem, speed) {
  if (!elem.style.opacity) {
    elem.style.opacity = 1;
  } // end if

  var outInterval = setInterval(function () {
    elem.style.opacity -= 0.02;
    if (elem.style.opacity <= 0) {
      clearInterval(outInterval);
      var inInterval = setInterval(function () {
        elem.style.opacity = Number(elem.style.opacity) + 0.02;
        if (elem.style.opacity >= 1) clearInterval(inInterval);
      }, speed / 50);
    } // end if
  }, speed / 50);
}
function isJson(str) {
  try {
    JSON.parse(str);
  } catch (e) {
    return true;
  }
  return false;
}
