/**
 * @file Esup-Pod Main JavaScripts
 */

/* exported getParents slideToggle fadeOut linkTo_UnCryptMailto showLoader videocheck send_form_data_vanilla */

// Read-only globals defined in video-script.html
/* global player */

// Read-only globals defined in video-edit.html
/* global VIDEO_MAX_UPLOAD_SIZE listext */

// this function (appendHTML) is not used elsewhere
/*
function appendHTML(node, html) {
  var temp = document.createElement("div");
  temp.innerHTML = html;
  var scripts = temp.getElementsByTagName("script");
  for (let i = 0; i < scripts.length; i++) {
    var script = scripts[i];
    var s = document.createElement("script");
    s.type = script.type || "text/javascript";
    if (script.src) {
      s.src = script.src;
    } else {
      s.text = script.text;
    }
    node.appendChild(s);
  }
}
*/
/**
 * [getParents description]
 * @param  {[type]} el             [description]
 * @param  {[type]} parentSelector [description]
 * @return {[type]}                [description]
 */
function getParents(el, parentSelector) {
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
  parents.push(parentSelector);
  return parents;
}

/**
 * Slide up target and remove it from DOM
 * @param  {[type]}   target   [description]
 */
function slideUpAndRemove(target) {
  target.animate({ opacity: 0 }, { duration: 1000 });
  slideUp(target, 1000, function () {
    target.remove();
  });
}

/**
 * Hide target element with a slide animation
 * @param  {[type]}   target   [description]
 * @param  {Number}   duration [description]
 * @param  {Function} callback [description]
 * @return {[type]}            [description]
 */
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
    if (callback !== null) {
      callback();
    }
  }, duration);
}

/**
 * Show target element with a slide animation
 * @param  {[type]}   target   [description]
 * @param  {Number}   duration [description]
 * @param  {Function} callback [description]
 * @return {[type]}            [description]
 */
var slideDown = (target, duration = 500) => {
  target.style.removeProperty("display");
  let display = window.getComputedStyle(target).display;
  if (display === "none") display = "block";
  target.style.display = display;
  let height = target.offsetHeight;
  target.style.overflow = "hidden";
  target.style.height = 0;
  target.style.paddingTop = 0;
  target.style.paddingBottom = 0;
  target.style.marginTop = 0;
  target.style.marginBottom = 0;
  target.offsetHeight;
  target.style.boxSizing = "border-box";
  target.style.transitionProperty = "height, margin, padding";
  target.style.transitionDuration = duration + "ms";
  target.style.height = height + "px";
  target.style.removeProperty("padding-top");
  target.style.removeProperty("padding-bottom");
  target.style.removeProperty("margin-top");
  target.style.removeProperty("margin-bottom");
  window.setTimeout(() => {
    target.style.removeProperty("height");
    target.style.removeProperty("overflow");
    target.style.removeProperty("transition-duration");
    target.style.removeProperty("transition-property");
  }, duration);
};

/**
 * [slideToggle description]
 * @param  {[type]} target   [description]
 * @param  {Number} duration [description]
 * @return {[type]}          [description]
 */
var slideToggle = (target, duration = 500) => {
  if (window.getComputedStyle(target).display === "none") {
    return slideDown(target, duration);
  } else {
    return slideUp(target, duration);
  }
};

/**
 * [fadeIn description]
 * @param  {[type]} el      [description]
 * @param  {[type]} display [description]
 * @return {[type]}         [description]
 */
function fadeIn(el, display) {
  el.style.opacity = 0;
  el.classList.remove("d-none");
  el.style.display = display || "block";
  (function fade() {
    var val = parseFloat(el.style.opacity);
    if (!((val += 0.1) > 1)) {
      el.style.opacity = val;
      requestAnimationFrame(fade);
    }
  })();
}

/**
 * [fadeOut description]
 * @param  {[type]} elem  [description]
 * @param  {[type]} speed [description]
 * @return {[type]}       [description]
 */
function fadeOut(elem, speed) {
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
/**
 * [isJson description]
 * @param  {[type]}  str [description]
 * @return {Boolean}     [description]
 */
function isJson(str) {
  try {
    JSON.parse(str);
  } catch (e) {
    return true;
  }
  return false;
}

/**
 * [linkTo_UnCryptMailto description]
 * @param  {[type]} s [description]
 * @return {[type]}   [description]
 */
function linkTo_UnCryptMailto(s) {
  location.href = "mailto:" + window.atob(s);
}

/**
 * [toHHMMSS description]
 * @return {[type]} [description]
 */
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

/**
 * Edit the iframe and share link code
 * @return {[type]} [description]
 */
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

if (document.getElementById("btn-download-qr-code") !== null) {
  document
    .getElementById("btn-download-qr-code")
    .addEventListener("click", (e) => {
      let nameOfDownload = e.target.dataset.slug + "-qrcode.png";
      downloadImage(document.getElementById("qrcode").src, nameOfDownload);
    });
}

/**
 * Download image function with url
 *
 * @param imageSrc Source of image
 * @param nameOfDownload Given name for download
 * @returns {Promise<void>}
 */
async function downloadImage(imageSrc, nameOfDownload = "default.png") {
  const response = await fetch(imageSrc);
  const blobImage = await response.blob();
  const href = URL.createObjectURL(blobImage);

  const anchorElement = document.createElement("a");
  anchorElement.href = href;
  anchorElement.download = nameOfDownload;

  document.body.appendChild(anchorElement);
  anchorElement.click();

  document.body.removeChild(anchorElement);
  window.URL.revokeObjectURL(href);
}

document.addEventListener("change", (e) => {
  if (e.target.id !== "displaytime") return;
  let displayTime = document.getElementById("displaytime");
  let txtpartage = document.getElementById("txtpartage");
  let txtinteg = document.getElementById("txtintegration");
  if (displayTime.checked) {
    if (txtpartage.value.indexOf("start") < 0) {
      txtpartage.value =
        txtpartage.value + "&start=" + parseInt(player.currentTime(), 10);

      if (txtpartage.value.indexOf("??") > 0)
        txtpartage.value = txtpartage.value.replace("??", "?");
      var valeur = txtinteg.value;
      txtinteg.value = valeur.replace(
        "/?",
        "/?start=" + parseInt(player.currentTime(), 10) + "&",
      );
    }
    document.getElementById("txtposition").value = player
      .currentTime()
      .toHHMMSS();
  } else {
    txtpartage.value = txtpartage.value
      .replace(/(&start=)\d+/, "")
      .replace(/(\start=)\d+/, "")
      .replace(/(\?start=)\d+/, "");

    txtpartage.valuex;
    txtinteg.value = txtinteg.value.replace(/(start=)\d+&/, "");
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

/**
 * USE TO SHOW THEME FROM CHANNELS
 * @param  {[type]}  tab                     [description]
 * @param  {[type]}  level                   [description]
 * @param  {[type]}  tab_selected            [description]
 * @param  {[type]}  tag_type                [description]
 * @param  {[type]}  li_class                [description]
 * @param  {[type]}  attrs                   [description]
 * @param  {[type]}  add_link                [description]
 * @param  {[type]}  current                 [description]
 * @param  {[type]}  channel                 [description]
 * @param  {Boolean} show_only_parent_themes [description]
 * @return {[type]}                          [description]
 */
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
  show_only_parent_themes = false,
  theme_parents = [],
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
  for (let i = 0; i < level; i++) prefix += "&nbsp;&nbsp;";
  if (level != 0) prefix += "|-";
  for (let i = 0; i < tab.length; i++) {
    var val = tab[i];
    var title = add_link
      ? '<a href="' + val.url + '">' + channel + " " + val.title + "</a>"
      : channel + " " + val.title;
    var selected =
      tab_selected.indexOf(val.id.toString()) > -1 ? "selected" : "";
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
        channel,
      );
    }
    if (
      count > 0 &&
      show_only_parent_themes &&
      theme_parents.includes(val.slug)
    ) {
      list += get_list(
        child,
        level + 1,
        tab_selected,
        tag_type,
        li_class,
        attrs,
        add_link,
        current,
        channel,
      );
    }
  }
  return list;
};

/* USERS IN NAVBAR */
if (typeof ownerBoxNavBar === "undefined") {
  var ownerBoxNavBar = document.getElementById("ownerboxnavbar");
} else {
  ownerBoxNavBar = document.getElementById("ownerboxnavbar");
}
if (ownerBoxNavBar) {
  let pod_users_list = document.getElementById("pod_users_list");
  ownerBoxNavBar.addEventListener("input", () => {
    if (ownerBoxNavBar.value && ownerBoxNavBar.value.length > 2) {
      var searchTerm = ownerBoxNavBar.value;
      getSearchListUsers(searchTerm).then((users) => {
        pod_users_list.textContent = "";
        users.forEach((user) => {
          pod_users_list.appendChild(createUserLink(user));
        });
      });
    } else {
      pod_users_list.textContent = "";
    }
  });
}

/**
 * Create link for user search
 * @param  {[type]} user [description]
 * @return {[type]}      [description]
 */
function createUserLink(user) {
  let li = document.createElement("li");
  let a = document.createElement("a");
  a.setAttribute("href", "/videos/?owner=" + user.username);
  a.setAttribute("title", user.first_name + " " + user.last_name);
  a.innerHTML =
    user.first_name + " " + user.last_name + " (" + user.username + ")";
  li.appendChild(a);
  return li;
}

/** COOKIE DIALOG **/

document.addEventListener("DOMContentLoaded", function () {
  let consent = Cookies.get("podCookieConsent");

  var cookieDiv = document.getElementById("cookieModal");
  if (cookieDiv) {
    var cookieModal = bootstrap.Modal.getOrCreateInstance(cookieDiv);
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
  }
});

/**
 * Enable / Disable buttons with specific condition parameter.
 *
 * @param  {HTMLElement}    element               HTML element to enable / disable
 * @param  {condition}      condition             Condition to evaluate for enabled disabled status
 */
function manageDisableBtn(element, condition) {
  condition
    ? element.removeAttribute("disabled")
    : element.setAttribute("disabled", "");
}
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
      if (mainContent != null) {
        document.getElementById("mainContent").classList.add("col-md-9");
      }
    });
    // Fired when #collapseAside has been hidden
    collapseAside.addEventListener("hidden.bs.collapse", function () {
      Cookies.set("activeCollapseAside", "close", { sameSite: "Lax" });

      // '<i class="bi bi-arrow-90deg-down"></i><i class="bi bi-list"></i>'
      let mainContent = document.getElementById("mainContent");

      if (mainContent != null) {
        document.getElementById("mainContent").classList.add("col-md-9");
      }
    });

    // If aside menu is empty, hide container and button
    if (collapseAside.querySelectorAll("div").length === 0) {
      if (collapseAside.offsetParent) {
        collapseAside.style.display = "none";

        collapseBoot.hide();
        // Destroy collapse object

        collapseBoot.dispose();

        let mainContent = document.getElementById("mainContent");
        if (mainContent) {
          document.getElementById("mainContent").classList.remove("col-md-9");
        }
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
    triggerAlertClose();
  }
});

/**
 * Automatically hide success and info type alerts
 *  generated by Django messages.add_message()
 */
function triggerAlertClose() {
  window.setTimeout(function () {
    document
      .querySelectorAll(
        "#base-message-alert>.alert-success, #base-message-alert>.alert-info",
      )
      .forEach((el) => {
        slideUpAndRemove(el);
      });
  }, 8000);
}

/**
 * SEARCH USER
 * @param  {[type]} searchTerm [description]
 * @return {[type]}            [description]
 */
async function getSearchListUsers(searchTerm) {
  try {
    let data = new FormData();
    data.append("term", searchTerm);
    data.append("csrfmiddlewaretoken", Cookies.get("csrftoken"));
    const response = await fetch("/ajax_calls/search_user/", {
      method: "POST",
      body: data,
      headers: {
        Accept: "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
    });
    const users = await response.json();
    return users;
  } catch (error) {
    showalert(gettext("User not found"), "alert-danger");
  }
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
  document.getElementById("fileModal_id_userpicture")?.remove();
});
document.addEventListener("submit", (e) => {
  if (e.target.id != "userpicture_form") return;

  e.preventDefault();
  let form = e.target;
  let data_form = new FormData(form);
  send_form_data(
    e.target.getAttribute("action"),
    data_form,
    "show_picture_form",
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
  if (e.target.id != "cancel_theme") return;
  document.querySelector("form.get_form_theme").style.display = "block";
  show_form_theme("");
  document.querySelectorAll("table_list_theme tr").forEach((el) => {
    el.classList.remove("table-primary");
  });

  window.scrollTo({
    top: parseInt(document.getElementById("list_theme").offsetTop, 10),
    behavior: "smooth",
  });
});
document.addEventListener("submit", (e) => {
  if (!e.target.classList.contains("get_form_theme")) return;
  e.preventDefault();

  let form = e.target;
  // Action can be new, modify or delete
  var action = form.querySelector("input[name=action]").value;
  let data_form = new FormData(form);
  if (action === "delete") {
    var deleteConfirm = confirm(
      interpolate(
        gettext("Are you sure you want to delete theme “%(title)s”?"),
        { title: form.dataset.title },
        true,
      ),
    );

    if (deleteConfirm) {
      send_form_data(window.location.href, data_form, "show_form_theme_delete");
    }
  } else {
    send_form_data(
      window.location.href,
      data_form,
      "show_form_theme_" + action,
    );
  }
});
/** VIDEO DEFAULT VERSION **/
document.addEventListener("change", (e) => {
  if (
    !e.target.matches("#video_version_form input[type=radio][name=version]")
  ) {
    return;
  }

  let submit_button = document.createElement("button");
  submit_button.style.display = "none";
  submit_button.type = "submit";
  document.getElementById("video_version_form").appendChild(submit_button);
  submit_button.click();
});
document.addEventListener("submit", (e) => {
  if (e.target.id != "video_version_form") return;
  e.preventDefault();
  let form = e.target;
  let data_form = new FormData(form);
  send_form_data(form.getAttribute("action"), data_form, "result_video_form");
});

/**
 * [result_video_form description]
 * @param  {[type]} data [description]
 * @return {[type]}      [description]
 */
var result_video_form = function (data) {
  if (data.errors) {
    showalert(
      gettext("One or more errors have been found in the form."),
      "alert-danger",
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
  callbackFail = undefined,
) {
  callbackSuccess =
    typeof callbackSuccess === "function"
      ? callbackSuccess
      : function ($data) {
          return $data;
        };
  callbackFail =
    typeof callbackFail === "function"
      ? callbackFail
      : function (xhr) {
          console.log(xhr);
        };

  // console.log("send_form_data. fct=" + fct);
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

  const options = {
    headers: {
      "X-Requested-With": "XMLHttpRequest",
    },
  };

  if (method === "post") {
    options.method = "POST";
    options.headers["X-CSRFToken"] = token;
    options.body = form_data;
  } else {
    options.method = "GET";
  }

  try {
    const response = await fetch(url, options);
    const data = await response.text();
    const processedData = callbackSuccess(data);
    if (method === "post") {
      window[fct](processedData);
    } else {
      if (typeof window[fct] === "function") {
        window[fct](processedData);
      }
    }
  } catch (error) {
    showalert(
      gettext("Error during exchange") +
        "(" +
        error +
        ")<br>" +
        gettext("No data could be stored."),
      "alert-danger",
    );

    callbackFail(error);
  }
};
/**
 * AJAX call function (usually send form data)
 *
 * @param  {String}          url               Address link to be requested
 * @param  {String}          fct               JS Function to call when it's done.
 * @param  {HTMLFormElement} [data_form]       The form to be sent with POST
 * @param  {String}          [method]          HTTP Request Method (GET or POST).
 * @param  {String}          [callbackSuccess] Function to call on success
 * @param  {String}          [callbackFail]    Function to call on failure
 * @return {String}          The raw response from the server
 */
var send_form_data_vanilla = function (
  url,
  fct,
  data_form = undefined,
  method = "post",
  callbackSuccess = undefined,
  callbackFail = undefined,
) {
  callbackSuccess =
    typeof callbackSuccess === "function"
      ? callbackSuccess
      : function (data) {
          return data;
        };
  callbackFail =
    typeof callbackFail === "function" ? callbackFail : function () {};
  if (data_form) {
    data_form = new FormData(data_form);
  }

  // console.log("Fetching "+url+"...");
  fetch(url, {
    method: method,
    body: data_form,
  })
    .then((response) => {
      if (response.ok) {
        return response.text();
      } else {
        throw new Error(`${response.status} : ${response.statusText}`);
      }
    })
    .then((data) => {
      // console.log("Success. data="+data);
      response = callbackSuccess(data);
      // console.log("Done. Calling "+fct+"...");
      window[fct](data);
    })
    .catch(function (err) {
      showalert(
        gettext("Error during exchange") +
          " (" +
          err +
          ")<br>" +
          gettext("No data could be stored."),
        "alert-danger",
      );
      callbackFail(err);
    });
};

/**
 * Called when creating a new theme
 * @param  {Array} data Theme data obtained from ajax call
 * @return {void}
 */
var show_form_theme_new = function (data) {
  if (data.indexOf("form_theme") === -1) {
    showalert(
      gettext("You are no longer authenticated. Please log in again."),
      "alert-danger",
    );
  } else {
    show_form_theme(data);
  }
};

/**
 * Called when starting a modify action on existing theme
 * @param  {Array} data Theme data obtained from ajax call
 * @return {void}
 */
var show_form_theme_modify = function (data) {
  if (data.indexOf("theme") === -1) {
    showalert(
      gettext("You are no longer authenticated. Please log in again."),
      "alert-danger",
    );
  } else {
    document
      .querySelectorAll("#table_list_theme tr")
      .forEach(function (trItem) {
        trItem.classList.remove("table-primary");
      });
    show_form_theme(data);
    data = new DOMParser().parseFromString(data, "text/html").body;
    // data.getElementById doesn't work here. Use data.querySelector()
    var id = data.querySelector("#id_theme").value;
    document.getElementById("theme_" + id).classList.add("table-primary");
  }
};

/**
 * Called when deleting a theme
 * @param  {Array} data Theme data obtained from ajax call
 * @return {void}
 */
var show_form_theme_delete = function (data) {
  if (!isJson(data)) {
    data = JSON.parse(data);
  }
  if (data.list_element) {
    show_list_theme(data.list_element);
    showalert(gettext("Theme sucessfully deleted."), "alert-success");
  } else {
    showalert(
      gettext("You are no longer authenticated. Please log in again."),
      "alert-warning",
    );
  }
};

/**
 * Display a form associated to the theme in data
 * @param  {Array} data Theme data obtained from ajax call
 * @return {void}
 */
var show_theme_form = function (data) {
  if (!isJson(data)) {
    data = JSON.parse(data);
  }
  if (data.list_element || data.form) {
    if (data.errors) {
      showalert(
        gettext("One or more errors have been found in the form."),
        "alert-danger",
      );
      show_form_theme(data.form);
    } else {
      show_form_theme("");
      document.querySelector("form.get_form_theme").style.display = "block";
      show_list_theme(data.list_element);
      showalert(gettext("Action performed successfully."), "alert-success");
    }
  } else {
    showalert(
      gettext("You are no longer authenticated. Please log in again."),
      "alert-danger",
    );
  }
};

/**
 * unused function? TODO : delete in 3.8.0
 * @param  {[type]} data [description]
 * @return {[type]}      [description]
 */
/*var show_picture_form = function (data) {
  let htmlData = new DOMParser().parseFromString(data, "text/html");
  document.getElementById("userpicture_form").innerHTML =
    htmlData.querySelector("#userpicture_form").innerHTML;
  let userpict = document.querySelector("#nav-usermenu .userpicture");
  if (
    htmlData.querySelector("#userpictureurl") &&
    htmlData.querySelector("#userpictureurl").value
  ) {
    userpict?.remove();
    document.querySelector("#nav-usermenu .userinitial").style.display = "none";
    document
      .querySelector("#nav-usermenu > button")
      .classList.remove("initials", "btn", "btn-primary");
    document.querySelector("#nav-usermenu > button").classList.add("nav-link");
    document
      .querySelector("#nav-usermenu > button")
      .insertAdjacentHTML(
        "beforeend",
        '<img src="' +
          htmlData.querySelector("#userpictureurl").value +
          '" class="userpicture rounded" alt="avatar" loading="lazy">',
      );
    //$(".get_form_userpicture").html($(".get_form_userpicture").children());
    document.querySelector(".get_form_userpicture").innerHTML =
      '<i class="bi bi-card-image pod-nav-link-icon d-lg-none d-xl-inline mx-1"></i>' +
      gettext("Change your picture");
  } else {
    userpict?.remove();

    document.querySelector("#nav-usermenu .userinitial").style.display =
      "inline-block";
    document
      .querySelector("#nav-usermenu > button")
      .classList.add("initials", "btn", "btn-primary");
    //$(".get_form_userpicture").html($(".get_form_userpicture").children());
    document.querySelector(".get_form_userpicture").innerHTML =
      '<i class="bi bi-card-image pod-nav-link-icon d-lg-none d-xl-inline mx-1"></i>' +
      gettext("Add your picture");
  }
  let userpicture = document.getElementById("userpictureModal");
  if (userpicture) {
    let userPictureModal = bootstrap.Modal.getOrCreateInstance(userpicture);
    userPictureModal.hide();
  }
}; */
var append_picture_form = async function (data) {
  let htmlData = new DOMParser().parseFromString(data, "text/html").body
    .firstChild;
  //$("body").append(data);
  document.body.appendChild(htmlData);
  htmlData.querySelectorAll("script").forEach((item) => {
    // run script tags of filewidget.js and custom_filewidget.js

    if (item.src) {
      let script = document.createElement("script");
      script.src = item.src;
      if (script.src.includes("filewidget.js"))
        document.body.appendChild(script);
    } else {
      if (item.id == "filewidget_script") (0, eval)(item.innerHTML);
    }
  });

  let userpicture = document.getElementById("userpictureModal");
  if (userpicture) {
    let userPictureModal = bootstrap.Modal.getOrCreateInstance(userpicture);
    userPictureModal.show();
  }
};
/**
 * [show_form_theme description]
 * @param  {[type]} data [description]
 * @return {[type]}      [description]
 */
function show_form_theme(data) {
  let div_form = document.getElementById("div_form_theme");
  div_form.style.display = "none";
  div_form.innerHTML = data;
  fadeIn(div_form);
  if (data != "")
    document.querySelector("form.get_form_theme").style.display = "none";
  window.scrollTo({
    top: parseInt(document.getElementById("div_form_theme").offsetTop, 10),
    behavior: "smooth",
  });
}
/**
 * [show_list_theme description]
 * @param  {[type]} data [description]
 * @return {[type]}      [description]
 */
function show_list_theme(data) {
  let list_theme = document.getElementById("list_theme");
  list_theme.style.display = "none";
  list_theme.innerHTML = data;
  fadeIn(list_theme);
  //$('form.get_form_theme').show();
  window.scrollTo({
    top: parseInt(document.getElementById("list_theme").offsetTop, 10),
    behavior: "smooth",
  });
}

/****** VIDEOS EDIT ******/

/*** Copy to clipboard ***/
if (typeof btnpartageprive === "undefined") {
  var btnpartageprive = document.getElementById("btnpartageprive");
} else {
  btnpartageprive = document.getElementById("btnpartageprive");
}
if (btnpartageprive) {
  btnpartageprive.addEventListener("click", function () {
    var copyText = document.getElementById("txtpartageprive");
    copyText.select();
    document.execCommand("copy");
    showalert(gettext("Text copied"), "alert-info");
  });
}

/** Restrict access **/
/** restrict access to group */
if (typeof id_is_restricted === "undefined") {
  var id_is_restricted = document.getElementById("id_is_restricted");
} else {
  id_is_restricted = document.getElementById("id_is_restricted");
}
if (id_is_restricted) {
  id_is_restricted.addEventListener("click", function () {
    restrict_access_to_groups();
  });
}
/**
 * [restrict_access_to_groups description]
 * @return {[type]} [description]
 */
var restrict_access_to_groups = function () {
  if (document.getElementById("id_is_restricted").checked) {
    let id_restricted_to_groups = document.getElementById(
      "id_restrict_access_to_groups",
    );
    id_restricted_to_groups.parentElement.classList.remove("d-none");
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
      "id_restrict_access_to_groups",
    );
    id_restricted_to_groups.parentElement.classList.add("d-none");
  }
};

if (typeof id_is_draft === "undefined") {
  var id_is_draft = document.getElementById("id_is_draft");
} else {
  id_is_draft = document.getElementById("id_is_draft");
}
if (id_is_draft) {
  id_is_draft.addEventListener("click", function () {
    restricted_access();
  });
}

/**
 * [restricted_access description]
 * @return {[type]} [description]
 */
var restricted_access = function () {
  document
    .querySelectorAll(".restricted_access")
    .forEach((restricted_access) => {
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
    });
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
            if (form.reportValidity() === false) {
              showalert(
                gettext("There are errors in the form, please correct them."),
                "alert-danger",
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
          false,
        );
      });
    },
    false,
  );
})();

/**
 * VIDEOCHECK FORM
 * @param  {[type]} form  [description]
 * @param  {[type]} event [description]
 * @return {[type]}       [description]
 */
var videocheck = function (form, event) {
  var fileInput = document.getElementById("id_video");
  if (fileInput && fileInput.files.length) {
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
          "alert-danger",
        );
        event.preventDefault();
        event.stopPropagation();
      } else {
        document.querySelector("#video_form fieldset").style.display = "none";
        document.querySelector("#video_form button").style.display = "none";

        let js_process = document.getElementById("js-process");
        js_process.classList.remove("d-none");
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
        "alert-danger",
      );
      event.preventDefault();
      event.stopPropagation();
    }
  }
};

/***** SHOW ALERT *****/
/**
 * Display an alert message
 * @param  {[type]} message   [The message to be displayed]
 * @param  {[type]} alertType Type of alert (info, success, danger, warning...)
 * @return {void}
 */
var showalert = function (message, alertType, idAlertType = "formalertdiv") {
  const icon_types = {
    "alert-success": "check-circle-fill",
    "alert-info": "info-fill",
    "alert-warning": "exclamation-triangle-fill",
    "alert-danger": "exclamation-triangle-fill",
  };

  let textHtml =
    "<div id=" +
    idAlertType +
    ' class="alert ' +
    alertType +
    ' alert-dismissible fade show" role="alert">' +
    '<i aria-hidden="true" class="bi bi-' +
    icon_types[alertType] +
    ' me-2"></i>' +
    '<span class="alert-message">' +
    message +
    "</span>" +
    '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="' +
    gettext("Close") +
    '"></button></div>';

  let parsedHTML = new DOMParser().parseFromString(textHtml, "text/html").body
    .firstChild;

  document.body.appendChild(parsedHTML);
  // Auto dismiss success and info types
  if (["alert-success", "alert-info"].includes(alertType)) {
    setTimeout(function () {
      let formalertdiv = document.getElementById(idAlertType);
      window.setTimeout(function () {
        slideUpAndRemove(formalertdiv);
      });
    }, 8000);
  }
};
// this function (show_messages) is not used elsewhere, there is no id "show_messages"
/*
function show_messages(msgText, msgClass, loadUrl) {
  var $msgContainer = document.getElementById("show_messages");
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
    setTimeout(function () {
      fadeOutIn($msgBox);
      if (loadUrl) {
        window.location.reload();
      } else {
        window.location.assign(loadUrl);
      }
    }, 4000);
  } else if (msgClass === "info" || msgClass === "success") {
    setTimeout(function () {
      fadeOutIn($msgBox);
      $msgBox.remove();
    }, 3000);
  }
}
*/

/***** MANAGE BOOTSTRAP LOADERS *****/
/**
 * Show or hide given loader
 * @param  {HTMLElement}  loaderElement     [Loader element to show]
 * @param  {boolean}      show              [True: enable full page loader / False: dismiss it]
 * @return {void}
 */
function showLoader(loaderElement, show) {
  if (show) {
    loaderElement.classList.remove("d-none");
    loaderElement.classList.remove("hide");
  } else {
    loaderElement.classList.add("hide");
    setTimeout(() => {
      loaderElement.classList.add("d-none");
    }, 150);
  }
}

/**
 * [flashing description]
 * @param  {[type]} elem     [description]
 * @param  {[type]} duration [description]
 * @return {[type]}          [description]
 */
function flashing(elem, duration) {
  elem.classList.add("flashing_field");
  setTimeout(function () {
    elem.classList.remove("flashing_field");
  }, duration);
}

// SEARCH INPUT //

document.addEventListener("DOMContentLoaded", function () {
  var searchInput = document.getElementById("s");
  var searchButton = document.getElementById("search-button");

  /**
   * Handles adding CSS classes to highlight the search element when it gains focus.
   */
  function handleFocus() {
    searchInput.classList.add("focus-search-input");
    searchInput.classList.remove("hide-search-input");
  }

  /**
   * Handles removing CSS classes to hide the search element when it loses focus.
   */
  function handleBlur() {
    searchInput.classList.remove("focus-search-input");
    searchInput.classList.add("hide-search-input");
  }
  if (searchButton) {
    searchButton.addEventListener("focus", handleFocus);
    searchButton.addEventListener("blur", handleBlur);
    searchInput.addEventListener("focus", handleFocus);
    searchInput.addEventListener("blur", handleBlur);
  }
});

/**
 * Removes double quotes from the start and end of the given text.
 *
 * @param {string} text - The input text to process.
 * @returns {string} The text without leading and trailing double quotes.
 */
function remove_quotes(text) {
  text = text.trim();
  if (text.charAt(0) === '"') {
    text = text.substring(1);
  }
  if (text.charAt(text.length - 1) === '"') {
    text = text.substring(0, text.length - 1);
  }
  return text;
}

let mainCollapseButton = document.getElementById("collapse-button");
mainCollapseButton.addEventListener("click", () => {
  window.scrollTo(0, 0);
});

/**
 * Remove accents and convert to lowercase.
 *
 * @param {string} str The string.
 *
 * @return {string} The new string.
 */
function removeAccentsAndLowerCase(str) {
  str = str.toLowerCase();
  return str.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

/**
 * Decode the string from the HTML entity.
 *
 * @param {string} str The string to decode.
 *
 * @return {string} The decoded string.
 */
function decodeString(str) {
  str = str.replace(/&#x([0-9A-Fa-f]+);/g, (match, p1) =>
    String.fromCharCode(parseInt(p1, 16)),
  );
  str = str.replace(/&#(\d+);/g, (match, p1) =>
    String.fromCharCode(parseInt(p1, 10)),
  );
  return str;
}
