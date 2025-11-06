/**
 * @file Esup-Pod File selector widget.
 * @since 2.5.0
 */

// Read-only globals defined in customfilewidget.html
/*
global id_input static_url deletefolder_url deletefile_url
*/

// Read-only globals defined in main.js
/*
global isJson fadeOut
*/

// Read-only globals defined in base.html
/*
global HIDE_USERNAME
*/


var list_folders_sub;
// change const to var to prevent multiple declaration
var loader = `
<div id="loader" class="d-flex justify-content-center align-items-center d-none loaderSpinner">
  <div class="spinner-border" role="status">
      <span class="visually-hidden">${gettext('Loading…')}</span>
  </div>
</div>
`;



if (typeof loaded == "undefined") {
  var loaded = true;

  document.addEventListener("click", (e) => {
    // Happens when a file is selected (example: select a thumbnail)
    if (!e.target.parentNode) return;
    if (
      !e.target.parentNode.matches(".file-name") &&
      !e.target.parentNode.matches(".file-image")
    )
      return;
    let file = e.target.parentNode;
    e.preventDefault();
    if (id_input && id_input != "") {
      document.getElementById(id_input).value = file.dataset.fileid;
      if (document.querySelector(".btn-fileinput_" + id_input)) {
        if (file.dataset.filetype == "CustomImageModel") {
          document.querySelector(".btn-fileinput_" + id_input).innerHTML =
            gettext("Change image");
        } else {
          document.querySelector(".btn-fileinput_" + id_input).innerHTML =
            gettext("Change file");
        }
      }

      //
      //if($(".btn-fileinput_"+id_input).text().indexOf(gettext('Change file')) != -1 || $(".btn-fileinput_"+id_input).text().indexOf(gettext('Select a file')) != -1)
      //    $(".btn-fileinput_"+id_input).html(gettext('Change file'));
      //else $(".btn-fileinput_"+id_input).html(gettext('Change image'));
      //
      document.getElementById("remove_file_" + id_input).style.display =
        "block";

      let html = "";
      if (file.dataset.filetype == "CustomImageModel") {
        html +=
          '<img src="' +
          file.getAttribute("href") +
          '" height="34" alt="' +
          file.getAttribute("title") +
          '" loading="lazy">&nbsp;';
      } else {
        html +=
          '<img style="height: 26px;vertical-align: middle;" src="' +
          static_url +
          'podfile/images/icons/default.svg" alt="" loading="lazy">&nbsp;';
      }
      html +=
        '<strong><a href="' +
        file.getAttribute("href") +
        '" target="_blank" title="' +
        gettext("Open file in a new tab") +
        '">' +
        file.getAttribute("title") +
        "</a></strong>&nbsp;";
      document.getElementById("fileinput_" + id_input).innerHTML = html;

      document.getElementById("modal-folder_" + id_input).textContent = "";

      let modalFile = bootstrap.Modal.getInstance(
        document.getElementById("fileModal_" + id_input)
      );
      modalFile.hide();
    }
  });


  document.addEventListener("click", (e) => {
    // Click on add or edit a folder
    if (
      !e.target.classList.contains("bi-pencil-square") &&
      !e.target.classList.contains("add-folder-btn")
    )
      return;

      // Check whether the second modal has already been initialised
      var secondModalElement = document.getElementById('folderModalCenter');
      var secondModal = bootstrap.Modal.getInstance(secondModalElement);
      if (!secondModal) {
          // Initialises the second modal with backdrop: false and keyboard: true
          secondModal = new bootstrap.Modal(secondModalElement, {
              backdrop: false,
              keyboard: true
          });
      }

      // Blur the first modal
      var modals = document.querySelectorAll('[id^="fileModal_id_"]');
      modals.forEach(function(modalElement) {
        const modalContentElementFirstModal = modalElement.querySelector(".modal-content");
        modalContentElementFirstModal.classList.add('blur-background');
      });

      // Adjusts the z-index of the second modal so that it appears above the first one.
      // Bootstrap uses z-indexes of 1050 for modals and 1040 for backdrops.
      // We need to set the second modal to a z-index higher than 1050 (e.g. 1055).
      secondModalElement.style.zIndex = 1055;

      // Display the second modal
      secondModal.show();
    });

   document.addEventListener("click", (e) => {
    if (
      !e.target.classList.contains("bi-share")
    )
      return;

      // Check whether the second modal has already been initialised
      var secondModalElement = document.getElementById('shareModalCenter');
      var secondModal = bootstrap.Modal.getInstance(secondModalElement);
      if (!secondModal) {
          // Initialises the second modal with backdrop: false and keyboard: true
          secondModal = new bootstrap.Modal(secondModalElement, {
              backdrop: false,
              keyboard: true
          });
      }

      // Blur the first modal
      var modals = document.querySelectorAll('[id^="fileModal_id_"]');
      modals.forEach(function(modalElement) {
        const modalContentElementFirstModal = modalElement.querySelector(".modal-content");
        modalContentElementFirstModal.classList.add('blur-background');
      });


      // Adjusts the z-index of the second modal so that it appears above the first one.
      secondModalElement.style.zIndex = 1055;

      // Display the second modal
      secondModal.show();
  });

  /*********** OPEN/CLOSE FOLDER MENU ************/
  document.addEventListener("click", (e) => {
    if (
      !e.target.classList.contains("folder") &&
      e.target.id != "close-folder-icon"
    )
      return;
    var bsdirs = new bootstrap.Collapse(document.getElementById("dirs"));
    bsdirs.hide();
  });

  document.addEventListener("change", (e) => {
    if (e.target.id != "ufile") return;
    submitFormFile(document.getElementById("formuploadfile"));
  });

  /****** CHANGE FILE ********/
  document.addEventListener("submit", (e) => {
    // Managed event: form submission to upload ou change a file/image.
    if (
      e.target.id != "formchangeimage" &&
      e.target.id != "formchangefile" &&
      e.target.id != "formuploadfile"
    )
      return;
    // Prevents normal submission
    e.preventDefault();
    submitFormFile(e.target);
  });

  /****** CHANGE FILE ********/
  document.addEventListener("hide.bs.modal", (event) => {
    // Managed event: close a modal window.
    if (
      event.target.id != "fileModal_id_thumbnail"
      && event.target.id != "fileModal_id_docment"
      && event.target.id != "shareModalCenter"
      && event.target.id != "folderModalCenter"
    ) return;
    event.stopPropagation();

    // When the second modal is closed, remove the blur from the first one.
    var modals = document.querySelectorAll('[id^="fileModal_id_"]');
    modals.forEach(function(modalElement) {
      const modalContentElementFirstModal = modalElement.querySelector(".modal-content");
      modalContentElementFirstModal.classList.remove('blur-background');
    });
  });

  document.addEventListener("show.bs.modal", (event) => {
    // Managed event: open the main modal window (#folderModalCenter).
    if (event.target.id != "folderModalCenter") return;
    event.stopPropagation();

    // Button that triggered the modal
    // Note: when multiple modal windows, the button is not targeted!
    let button = event.relatedTarget;

    let modal = event.target;
    modal.querySelectorAll("form").forEach((e) => {
      e.style.display = "none";
    });

    // Worjing variables
    let folder_id = null;
    let fileid = null;
    let filename = null;
    let filetype = null;

    if (button) {
      // Default source code: useful when only one modal is used
      folder_id = button.dataset.folderid;
      fileid = button.dataset.fileid;
      filename = button.dataset.filename;
      filetype = button.dataset.filetype;
    } else {
      // Modified source code: useful when multiple modal windows are used
      // Retrieve the stored trigger element (see setModalAction() function)
      const triggerAction = document.getElementById("folderModalCenter").getAttribute('data-trigger-action');
      const triggerFolder = document.getElementById("folderModalCenter").getAttribute('data-trigger-folder');
      const triggerId = document.getElementById("folderModalCenter").getAttribute('data-trigger-id');
      const triggerName = document.getElementById("folderModalCenter").getAttribute('data-trigger-name');
      const triggerType = document.getElementById("folderModalCenter").getAttribute('data-trigger-type');

      // triggerAction can be: addfolder, currentfolderrename, currentfilerename
      if (triggerAction) {
        // Retrieve the targeted button
        button = document.getElementById(triggerAction);
        // Get data from the stored rigger
        folder_id = triggerFolder;
        fileid = triggerId;
        filename = triggerName;
        filetype = triggerType;
      }
      // Clear trigger data
      document.getElementById("folderModalCenter").removeAttribute('data-trigger-action');
      document.getElementById("folderModalCenter").removeAttribute('data-trigger-folder');
      document.getElementById("folderModalCenter").removeAttribute('data-trigger-id');
      document.getElementById("folderModalCenter").removeAttribute('data-trigger-name');
      document.getElementById("folderModalCenter").removeAttribute('data-trigger-type');
    }

    switch (filetype) {
      case "CustomImageModel":
        var modalTitle = gettext("Change image “%s”");
        document.getElementById("folderModalCenterTitle").innerHTML = interpolate(
          modalTitle, [filename]
        );
        modal.querySelectorAll(".modal-body input#id_folder").forEach((e) => {
          e.value = folder_id;
        });
        modal.querySelectorAll(".modal-body input#id_image").forEach((e) => {
          e.value = fileid;
        });
        modal.querySelectorAll(".modal-body input#file_id").forEach((e) => {
          e.value = fileid;
        });
        modal.querySelectorAll(".modal-body input#file_type").forEach((e) => {
          e.value = filetype;
        });
        document.getElementById("formchangeimage").style.display = "block";
        break;
      case "CustomFileModel":
        var modalTitle = gettext("Change file “%s”");
        document.getElementById("folderModalCenterTitle").innerHTML =
          interpolate(modalTitle, [filename]);
        modal.querySelectorAll(".modal-body input#id_folder").forEach((e) => {
          e.value = folder_id;
        });
        modal.querySelectorAll(".modal-body input#file_id").forEach((e) => {
          e.value = fileid;
        });
        modal.querySelectorAll(".modal-body input#file_type").forEach((e) => {
          e.value = filetype;
        });

        document.getElementById("formchangefile").style.display = "block";
        break;
      default: // Extract info from data-* attributes
        document.getElementById("folderFormName").style.display = "block";
        document.getElementById("folderModalCenterTitle").textContent = gettext(
          "Enter new name of folder"
        );
        var oldname = button.dataset.oldname;
        // If necessary, you could initiate an AJAX request here (and then do the updating in a callback).
        // Update the modal's content. We'll use jQuery here, but you could use a data binding library or other methods instead.
        var folder_input = modal.querySelector("#folderInputName");
        folder_input.value = oldname;
        var focus = new Event("focus");
        folder_input.dispatchEvent(focus);
        modal.querySelector(".modal-body input#formfolderid").value = folder_id;
        break;
    }
  });

  /**
   * Creates a user list item elements
   *
   * @param {string} text - The text content of the button.
   * @param {User} elt - The user object.
   * @param {string} type - The type of action ("Add" or "Remove").
   * @returns {HTMLElement} The list item.
   */
  function user_li(text, elt, type) {
    let cls =
    type.toLowerCase() === "add"
      ? "btn-success btn-add"
      : "btn-danger btn-remove";
    const li = document.createElement("li");
    li.classList.add("list-group-item");

    const span = document.createElement("span");
    span.classList.add("username");
    span.textContent = `${elt.first_name} ${elt.last_name} ${!HIDE_USERNAME ? "(" + elt.username + ")" : ""}`;

    const a  = document.createElement("a");
    a.href = "#";
    a.role = "button";
    a.dataset.userid = elt.id;
    a.classList.add("btn", "btn-share");
    a.classList.add(...cls.split(" "));
    a.textContent = text;

    li.appendChild(span);
    li.appendChild(a);
    return li;
  }

  /**
   * Creates a list item element in case of empty user list.
   */
  function emptyUserLi() {
    const li = document.createElement("li");
    li.classList.add("list-group-item");

    const span = document.createElement("span");
    span.classList.add("empty-user-text");
    span.textContent = gettext("No user found");
    li.appendChild(span);
    return li;
  }

  function reloadRemoveBtn() {
    let remove = gettext("Remove");
    const sharedPeopleContainer = document.getElementById("shared-people");
    sharedPeopleContainer.textContent = "";
    const foldId = document.getElementById("formuserid").value;
    const url = "/podfile/ajax_calls/folder_shared_with?foldid=" + foldId;
    const token = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

    fetch(url, {
      method: "GET",
      headers: {
        "X-CSRFToken": token,
        "X-Requested-With": "XMLHttpRequest",
        Authorization: "Bearer " + token,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.length > 0) {
          data.forEach((elt) => {
            const listItem = user_li(remove, elt, "remove");
            sharedPeopleContainer.appendChild(listItem);
          });
        }
      })
      .catch((error) => {
        showalert(gettext("Server error") + "<br>" + error, "alert-danger");
      });
  }

  function reloadAddBtn(searchTerm) {
    const formUserId = document.getElementById("formuserid");
    if (!formUserId) return;

    const folderId = Number.parseInt(formUserId.value, 10);
    const add = gettext("Add");
    const url = "/podfile/ajax_calls/search_share_user?term=" + searchTerm + "&foldid=" + folderId;
    const token = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

    fetch(url, {
      method: "GET",
      headers: {
        "X-CSRFToken": token,
        "X-Requested-With": "XMLHttpRequest",
        Authorization: "Bearer " + token,
      },
      cache: "no-cache",
    })
      .then((response) => response.json())
      .then((data) => {
        const userSearchContainer = document.getElementById("user-search");
        userSearchContainer.textContent = "";
        if (data.length === 0) {
          userSearchContainer.appendChild(emptyUserLi());
        } else {
          data.forEach((elt) => {
            const listItem = user_li(add, elt, "add");
            userSearchContainer.appendChild(listItem);
          });
        }
        userSearchContainer.classList.remove("d-none");
      })
      .catch((error) => {
        showalert(gettext("Server error") + "<br>" + error, "alert-danger");
      });
  }

  //$(document).on('click', '#currentfoldershare', function(e){
  document.addEventListener("hide.bs.modal", (event) => {
    if (event.target.id != "shareModalCenter") return;
    event.stopPropagation();
  });
  document.addEventListener("show.bs.modal", (event) => {
    // Managed event: click on Share
    if (event.target.id != "shareModalCenter") return;
    event.stopPropagation();
    document.getElementById("user-search").classList.add("d-none");
    document.getElementById("shared-people").textContent = "";
    let button = event.relatedTarget;
    var folder_id = "";
    var modal = "";
    if (button) {
      // If target is the <button>
      folder_id = button.dataset.folderid;
      modal = document.querySelector(button.dataset.bsTarget);
    } else {
      // If target is the <i> and not the <button>
      let button_share = document.getElementById("currentfoldershare");
      folder_id = button_share.dataset.folderid;
      modal = document.querySelector("#shareModalCenter");
    }
    modal.querySelector("#formuserid").value = folder_id;
    reloadRemoveBtn();
  });


  document.addEventListener("click", (e) => {
    if (!e.target.classList.contains("btn-remove")) return;
    let url =
      "/podfile/ajax_calls/remove_shared_user?foldid=" +
      document.getElementById("formuserid").value +
      "&userid=" +
      e.target.dataset.userid;
    let token = document.querySelector(
      'input[name="csrfmiddlewaretoken"]'
    ).value;
    fetch(url, {
      method: "GET",
      headers: {
        "X-CSRFToken": token,
        Authorization: "Bearer " + token,
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/json",
      },
      cache: "no-cache",
    })
      .then((response) => {
        if (response.status === 201) {
          reloadRemoveBtn();
        } else {
          showalert(
            gettext("Server error") + "<br>" + response.statusText,
            "alert-danger"
          );
        }
      })
      .catch((error) => {
        showalert(gettext("Server error") + "<br>" + error, "alert-danger");
      });
  });

  document.addEventListener("click", (e) => {
    if (!e.target.classList.contains("btn-add")) return;
    let url =
      "/podfile/ajax_calls/add_shared_user?foldid=" +
      document.getElementById("formuserid").value +
      "&userid=" +
      e.target.dataset.userid;
    let token = document.querySelector(
      'input[name="csrfmiddlewaretoken"]'
    ).value;

    fetch(url, {
      method: "GET",
      headers: {
        "X-CSRFToken": token,
        Authorization: "Bearer " + token,
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/json",
      },
      cache: "no-cache",
    })
      .then((response) => {
        if (response.status == 201) {
          reloadAddBtn(document.getElementById("userInputName").value);
          reloadRemoveBtn();
        } else {
          showalert(
            gettext("Server error") + "<br>" + response.statusText,
            "alert-danger"
          );
        }
      })
      .catch((error) => {
        showalert(gettext("Server error") + "<br>" + error, "alert-danger");
      });
  });

  document.addEventListener("click", (e) => {
    if (e.target.id != "modalSave") return;
    document.querySelectorAll("#folderModalCenter form").forEach((form) => {
      if (form.style.display == "none") return;
      let button = document.createElement("button");
      button.type = "submit";
      button.style.display = "none";
      form.append(button);
      button.click();
    });
  });

  document.addEventListener("click", (e) => {
    // Managed event: click to delete a folder
    var contain_target = false;
    if (document.getElementById("currentfolderdelete")) {
      contain_target = document.getElementById("currentfolderdelete").contains(e.target);
    }
    if (e.target.id == "currentfolderdelete" || contain_target) {
      var deleteConfirm = confirm(
        gettext("Are you sure you want to delete this folder?")
      );
      if (deleteConfirm) {
        var id = e.target.dataset.folderid;
        var csrfmiddlewaretoken = "";
        if (id) {
          // If target is the <button>
          csrfmiddlewaretoken = e.target.querySelector(
            'input[name="csrfmiddlewaretoken"]'
          ).value;
        } else {
          // If target is the <i> and not the <button>
          let button_delete = document.getElementById("currentfolderdelete");
          id = button_delete.dataset.folderid;
          csrfmiddlewaretoken = button_delete.querySelector(
            'input[name="csrfmiddlewaretoken"]'
          ).value;
        }
        send_form_data(
          deletefolder_url,
          { id: id, csrfmiddlewaretoken: csrfmiddlewaretoken },
          "reloadFolder"
        );
      }
    }
  });

  document.addEventListener("click", (e) => {
    //if (!e.target.classList.contains("btn-delete-file")) return;
    if (e.target.classList.contains("btn-delete-file") || (e.target.parentNode && e.target.parentNode.classList.contains("btn-delete-file"))) {
      var deleteConfirm = confirm(
        gettext("Are you sure you want to delete this file?")
      );
      if (deleteConfirm) {
        const buttonElement = e.target.closest("button.btn-delete-file");
        let id = buttonElement.dataset.fileid;
        let classname = buttonElement.dataset.filetype;
        // Manage type to avoid a bug when select a file/image after a deletion
        let type = buttonElement.dataset.type;
        let csrfmiddlewaretoken = buttonElement.querySelector("input").value;
        send_form_data(
          deletefile_url,
          {
            id: id,
            classname: classname,
            type: type,
            csrfmiddlewaretoken: csrfmiddlewaretoken,
          },
          "show_folder_files"
        );
      }
    }
  });

  document.addEventListener("submit", (e) => {
    // Managed event: click to add or edit a folder
    if (e.target.id != "folderFormName") return;
    e.preventDefault();
    let form = e.target;
    let data_form = new FormData(form);
    send_form_data(form.getAttribute("action"), data_form, "reloadFolder");
  });

  document.addEventListener("input", (e) => {
    if (e.target.id != "folder-search") return;
    var text = e.target.value.toLowerCase();
    if (folder_searching === true) {
      return;
    } else {
      if (text.length > 2 || text.length === 0) {
        getFolders(text);
      }
    }
  });

  document.addEventListener("input", (e) => {
    if (e.target.id != "userInputName") return;

    if (e.target.value && e.target.value.length > 2) {
      var searchTerm = e.target.value;
      reloadAddBtn(searchTerm);
    } else {
      let user_search = document.getElementById("user_search");
      if (user_search) {
        user_search.textContent = "";
        fadeOut(user_search, 300);
        setTimeout(() => {
          user_search.hide();
        }, 300);
      }
    }
  });

  function reloadFolder(data) {
    if (!isJson(data)) data = JSON.parse(data);
    if (data.list_element) {
      var folder_id = data.folder_id;

      if (data.new_folder === true && document.getElementById("list_folders_sub")) {
        let type = document.getElementById("list_folders_sub").dataset.type;

        let string_html =
          '<div class="folder_container text-truncate">' +
          createFolder(
            data.folder_id,
            data.folder_name,
            true,
            type,
            undefined
          ) +
          "</div>";
        let parsedHTML = new DOMParser().parseFromString(
          string_html,
          "text/html"
        ).body.firstChild;

        document
          .getElementById("list_folders_sub")
          .insertBefore(
            parsedHTML,
            document.getElementById("list_folders_sub").firstChild
          );
      }

      if (data.folder_name && document.getElementById("folder-name-" + folder_id)) {
        document.getElementById("folder-name-" + folder_id).textContent = data.folder_name;
      }

      if (data.deleted && document.getElementById("folder_" + data.deleted_id)) {
        document.getElementById("folder_" + data.deleted_id).remove();
      }
      send_form_data(
        "/podfile/get_folder_files/" + folder_id,
        {
          type: type
        },
        "show_folder_files",
        "get"
      );
      // Dismiss modal
      let center_mod = document.getElementById("folderModalCenter");
      let center_modal = bootstrap.Modal.getOrCreateInstance(center_mod);
      center_modal.hide();
      center_mod.querySelector("#folderInputName").value = "";
      center_mod.querySelector("#formfolderid").value = "";
    } else {
      if (data.includes(gettext("Two folders cannot have the same name."))) {
        showalert(
          gettext("Two folders cannot have the same name."),
          "alert-danger"
        );
      } else {
        showalert(
          gettext("You are no longer authenticated. Please log in again."),
          "alert-danger"
        );
      }
    }
  }

  function show_folder_files(data) {
    if (!isJson(data)) data = JSON.parse(data);

    document.getElementById("files").classList.remove("loading");
    if (data.list_element) {
      document.getElementById("files").innerHTML = data.list_element;
      if ("emptyfoldermsg" in data) {
        document.getElementById("listfiles").innerHTML = data.emptyfoldermsg;
      }
      document.querySelectorAll(".list_folders a").forEach((elt) => {
        elt.classList.remove("font-weight-bold");
      });
      document.querySelectorAll("img.directory-image").forEach((elt) => {
        elt.src = static_url + "podfile/images/folder.png";
      });
      document.querySelectorAll("img.file-image").forEach((elt) => {
        elt.src = static_url + "podfile/images/home_folders.png";
      });
      let folder_id = document.getElementById("folder_" + data.folder_id);
      if (folder_id) {
        document
          .getElementById("folder_" + data.folder_id)
          .classList.add("font-weight-bold");
      }

      let folder = document.getElementById("folder_" + data.folder_id + " img");
      if (folder) folder.src = static_url + "podfile/images/opened_folder.png";

      // Dismiss modal
      let center_modal = document.getElementById("folderModalCenter");
      let center_modal_instance = bootstrap.Modal.getOrCreateInstance(center_modal);
      center_modal_instance.hide();
      center_modal.querySelector("#folderInputName").value = "";
      center_modal.querySelector("#formfolderid").value = "";

      if (data.upload_errors && data.upload_errors != "") {
        const str = data.upload_errors.split("\n").join("<br>");
        showalert(
          gettext("Error during exchange") + "<br>" + str,
          "alert-danger"
        );
      }
    } else {
      if (data.errors) {
        showalert(data.errors + "<br>" + data.form_error, "alert-danger");
      } else {
        showalert(
          gettext("You are no longer authenticated. Please log in again."),
          "alert-danger"
        );
      }
    }
  }

  /* exported append_folder_html_in_modal */
  function append_folder_html_in_modal(data) {
    document.getElementById("modal-folder_" + id_input).innerHTML = data;
    getFolders("");
    folder_observer = add_folder_observer();
    folder_observer.observe(list_folders_sub, { childList: true, subtree: true });
  }

  function getCurrentSessionFolder() {
    let folder = "home";
    let url = "/podfile/ajax_calls/current_session_folder/";

    let token = document.querySelector(
      'input[name="csrfmiddlewaretoken"]'
    ).value;
    fetch(url, {
      method: "GET",
      headers: {
        "X-CSRFToken": token,
        Authorization: "Bearer " + token,
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then((response) => response.json())
      .then((data) => {
        folder = data.folder;
      })
      .catch(() => {});
    return folder;
  }

  var folder_open_icon = `<i class="folder-open bi bi-folder2-open" id="folder-open-icon"></i>`;
  var folder_icon = `<i class="folder-close bi bi-folder2"></i>`;

  function createFolder(foldid, foldname, isCurrent, type, owner = undefined) {
    let construct = "";
    construct +=
      '<a href="#" class="folder ' +
      (isCurrent ? "font-weight-bold folder-opened" : "") +
      ' " id="folder_' +
      foldid +
      '" data-foldname="' +
      foldname +
      '" data-id="' +
      foldid +
      '" data-target="';
    let isType = type != "None" && type != undefined;
    construct +=
      "/podfile/get_folder_files/" +
      foldid +
      (isType ? "?type=" + type : "") +
      '">';
    if (owner != undefined) {
      foldname =
        '<span class="folder_name" id="folder-name-' +
        foldid +
        '">' +
        foldname +
        "</span> <span><b>(" +
        owner +
        ")</b></span>";
    } else {
      foldname =
        '<span class="folder_name" id="folder-name-' +
        foldid +
        '">' +
        foldname +
        "</span>";
    }
    construct += `${folder_open_icon} ${folder_icon} ${foldname}</a>`;
    return construct;
  }
  // **********************************************************************
  var folder_searching = false;
  function add_folder_observer() {
    // The new observer with a callback to execute upon change
    list_folders_sub = document.getElementById("list_folders_sub");
    var folder_observer = new MutationObserver((mutationsList) => {
      if(document.getElementById("more")) {
        document.getElementById("more").addEventListener("click", (event) => {
          event.preventDefault();
          seemore(event);
        });
      }
      document
        .querySelectorAll("a.folder")
        .forEach(el => {
          el.addEventListener("click", (event) => {
            event.preventDefault();
            showfiles(event);
          });
        });
    });
    return folder_observer;
  }


  function getFolders(search = "") {
    document.getElementById("list_folders_sub").textContent = "";
    let type = document.getElementById("list_folders_sub").dataset.type;
    let currentFolder = getCurrentSessionFolder();
    let url = "/podfile/ajax_calls/user_folders";
    if(search !== ""){
      url += "?search=" + search;
    }
    let token = document.querySelector(
      'input[name="csrfmiddlewaretoken"]'
    ).value;
    folder_searching = true;
    fetch(url, {
      method: "GET",
      headers: {
        "X-CSRFToken": token,
        Authorization: "Bearer " + token,
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then((response) => response.json())
      .then((data) => {
        let nextPage = data.next_page;
        data.folders.forEach((elt) => {
          let string_html =
            '<div class="folder_container text-truncate">' +
            createFolder(
              elt.id,
              elt.name,
              currentFolder == elt.name,
              type,
              elt.owner
            ) +
            "</div>";
          let parsedHTML = new DOMParser().parseFromString(
            string_html,
            "text/html"
          ).body.firstChild;
          const listFoldersSub = document.getElementById("list_folders_sub");
          if (listFoldersSub) {
            listFoldersSub.appendChild(parsedHTML);
          }
        });
        if (nextPage != -1) {
          search = data.search !== "" ? data.search : null;
          document
            .getElementById("list_folders_sub")
            .innerHTML += (
              seeMoreElement(nextPage, data.current_page + 1, data.total_pages, search)
            );
        }
        folder_searching = false;
      }).catch((error) => {
        showalert(gettext("Server error") + "<br>" + error, "alert-danger");
      });
  }

  /*** load folder after dom charged and check for changing **** */
  document.addEventListener("DOMContentLoaded", () => {
    if (typeof myFilesView !== "undefined") {
      getFolders("");
      var folder_observer = add_folder_observer();
      folder_observer.observe(list_folders_sub, { childList: true, subtree: true });
    }
  });
  /********************************** */

  var seeMoreElement = function (nextPage, curr_page, tot_page, search = null) {
    search = search ? `&search=${search}` : "";
    let seeMore = gettext("See more");
    return `
      <div class="view-more-container m-2">
        <a id="more" class="btn btn-light href="#" data-next="/podfile/ajax_calls/user_folders?page=${nextPage}${search}">
          <i class="bi bi-arrow-down-square" aria-hidden="true"></i>
          <span class="text">${seeMore} (${curr_page}/${tot_page})</span>
        </a>
        ${loader}
      </div>
    `;
  };

  function seemore() {
    let parent_el = document.getElementById("more").parentNode;
    showLoader(parent_el.querySelector("#loader"), true);
    let next = document.getElementById("more").dataset.next;
    let search = document.getElementById("more").dataset.search;
    let currentFolder = getCurrentSessionFolder();
    let type = document.getElementById("list_folders_sub").dataset.type;
    let url = next;
    let token = document.querySelector(
      'input[name="csrfmiddlewaretoken"]'
    ).value;
    folder_searching = true;
    fetch(url, {
      method: "GET",
      headers: {
        "X-CSRFToken": token,
        Authorization: "Bearer " + token,
        "X-Requested-With": "XMLHttpRequest",
      },
      cache: "no-cache",
    })
      .then((response) => response.json())
      .then((data) => {
        parent_el.remove();
        let nextPage = data.next_page;
        data.folders.forEach((elt) => {
          let string_html =
            '<div class="folder_container text-truncate">' +
            createFolder(
              elt.id,
              elt.name,
              currentFolder == elt.name,
              type,
              elt.owner
            ) +
            "</div>";
          let parsedHTML = new DOMParser().parseFromString(
            string_html,
            "text/html"
          ).body.firstChild;
          document.getElementById("list_folders_sub").appendChild(parsedHTML);
        });
        if (nextPage != -1) {
          search = data.search !== "" ? data.search : null;
          document
            .getElementById("list_folders_sub")
            .innerHTML += (
              seeMoreElement(nextPage, data.current_page + 1, data.total_pages, search)
            );
        }
        folder_searching = false;
      });
  }

  function showfiles(e) {
    let cible = e.target;
    if (e.target.nodeName.toLowerCase() !== "a" ) {
      cible = e.target.parentNode;
    }
    document
      .querySelectorAll("#podfile #list_folders_sub a.folder-opened")
      .forEach((el) => {
        el.classList.remove("folder-opened");
      });
    cible.classList.add("folder-opened");


    document.getElementById("files").classList.add("loading");
    // let id = cible.dataset.id;

    document.getElementById("files").innerHTML = loader;

    let success_func = function ($data) {
      $data = JSON.parse($data);
      let html = document.createElement("div");
      html.innerHTML = $data.list_element;
      let listfiles = html.querySelector("#listfiles");
      if (listfiles.childNodes.length === 0) {
        let emptyFolderMsg = `
              <div class="empty-folder-warning">
                  ${gettext("This folder is empty")}
              </div>
              `;
        $data["emptyfoldermsg"] = emptyFolderMsg;
      }
      return $data;
    };
    let error_func = function () {};
    send_form_data(
      cible.dataset.target,
      {},
      "show_folder_files",
      "get",
      success_func,
      error_func
    );
  }
/*
  document.addEventListener("show.bs.modal", (event) => {
    if (!event.target.matches(".podfilemodal")) return;
    event.stopPropagation();
    setTimeout(function () {
      getFolders("");
    }, 500);
  });
*/
}

/**
 * Handles the submission of a form containing file data via an AJAX request.
 *
 * This function hides the target form, displays a loading indicator, and sends the form data
 * to the server using the Fetch API. Upon receiving a response, it updates the UI to reflect
 * the result of the operation. If an error occurs during the request, it displays an error alert.
 *
 * @param {HTMLFormElement} target - The form element being submitted. It must have an "action" attribute
 *                                   specifying the URL to which the form data will be sent.
 *
 * @returns {void}
 *
 * @throws {Error} If the fetch request fails, an error message is displayed to the user.
 *
 * @example
 * // Assuming there is a form element with id "uploadForm" in the DOM:
 * const form = document.getElementById("uploadForm");
 * submitFormFile(form);
 */
function submitFormFile(target) {
  target.style.display = "none";
  document.querySelectorAll(".loadingformfiles").forEach((el) => {
    el.style.display = "block";
  });
  document.getElementById("listfiles").style.display = "none";

  var data_form = new FormData(target);

  // Use of specific attribute for AJAX requests, to avoid to submit twice
  var url = target.getAttribute("action-for-ajax");
  // Default behaviour for NON AJAX requests
  if (!url) { url = target.getAttribute("action"); }
  fetch(url, {
    method: "POST",
    body: data_form,
    processData: false,
    contentType: false,
    headers: {
      'X-Requested-With': 'XMLHttpRequest', // Necessary to work with is_ajax
    },
  })
    .then((response) => response.json())
    .then((data) => {
      document.querySelectorAll(".loadingformfiles").forEach((el) => {
        el.style.display = "none";
      });
      document.getElementById("listfiles").style.display = "block";
      target.style.display = "block";
      show_folder_files(data);
    })

    .catch((error) => {
      target.style.display = "block";
      document.querySelectorAll(".loadingformfiles").forEach((el) => {
        el.style.display = "none";
      });
      document.getElementById("listfiles").style.display = "block";
      var data = error.status + " " + error.statusText;

      showalert(
        gettext("Error during exchange") +
        "(" +
        data +
        ")<br>" +
        gettext("No data could be stored."),
        "alert-danger"
      );
    });
}

/**
 * Sets up modal action by storing trigger element data as attributes in the target modal.
 * Used to pass context (file/folder information) between modals in a multi-step interface.
 *
 * @param {string} action - The action to be performed ('currentfolderrename', 'currentfilerename', 'addfolder').
 * @param {string} folder - The target folder path (default: empty string).
 * @param {string} id - The unique identifier of the file/image (default: empty string).
 * @param {string} name - The display name of the file/image (default: empty string).
 * @param {string} type - The type of item ('file' or 'image') (default: empty string).
 */
function setModalAction(action, folder = "", id = "", name = "", type = "") {
  // Get reference to the secondary modal element
  const secondModal = document.getElementById('folderModalCenter');

  // Store trigger element's data as custom attributes on the modal
  if (secondModal) {
    secondModal.setAttribute('data-trigger-action', action);
    secondModal.setAttribute('data-trigger-folder', folder);
    secondModal.setAttribute('data-trigger-id', id);
    secondModal.setAttribute('data-trigger-name', name);
    secondModal.setAttribute('data-trigger-type', type);
  }
}
