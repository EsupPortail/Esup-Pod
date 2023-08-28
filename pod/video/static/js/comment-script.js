/**
 * comment-scripts.js
 * Handle comments under a video in Esup-Pod
 */

const base_vote_url = base_url.replace("comment", "comment/vote");
const base_delete_url = base_url.replace("comment", "comment/del");
let all_comment = null;
const lang_btn = document.querySelector(".btn-lang.btn-lang-active");
const comment_title = document.querySelector(".comment_title");
// Loader Element
const loader = document.querySelector(".lds-ring");
let VOTED_COMMENTS = [];
const COLORS = [
  "rgb(15,166,2)",
  "sienna",
  "#f44040",
  "teal",
  "darkorchid",
  "orange",
  "yellowgreen",
  "steelblue",
  "darkgray",
];
const LANG = lang_btn ? lang_btn.textContent.trim() : "fr";
dayjs.extend(dayjs_plugin_relativeTime);
dayjs.locale(LANG);

const ACTION_COMMENT = {
  comment_to_delete: null,
};
const answer_sing = gettext("Answer");
const answer_plural = gettext("Answers");

if (!is_authenticated)
  document.querySelector(".comment_counter_container").style.margin =
    "0 0 1em 0";

/*class AlertMessage extends HTMLElement {
  constructor(message, alert_class = "success") {
    super();
    this.setAttribute("class", "alert alert-dismissible fade show alert-" + alert_class);
    this.setAttribute("role", "alert");
    this.alert_class = alert_class;
    let html = document.createElement("DIV");
    html.setAttribute("class", "alert_content");
    html.innerHTML = message +
    '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="' +
      gettext("Close") +
      '"></button></div>';
    this.appendChild(html);
  }
  connectedCallback() {
    super.connectedCallback && super.connectedCallback();
    let show_duration = this.alert_class == "success" ? 3000:6000;
    window.setTimeout(() => {
      this.classList.add("alert_close");
      window.setTimeout(() => {
        this.parentElement.removeChild(this);
      }, 1000);
    }, show_duration);
  }
}
customElements.define("alert-message", AlertMessage);*/

class ConfirmModal extends HTMLElement {
  constructor(
    title = null,
    message = null,
    delete_text = null,
    cancel_text = null,
  ) {
    super();

    title = title ? title : this.getAttribute("confirm_title");
    message = message ? message : this.getAttribute("message");
    delete_text = delete_text ? delete_text : this.getAttribute("delete_text");
    cancel_text = cancel_text ? cancel_text : this.getAttribute("cancel_text");
    const close_text = gettext("Close");

    let modal = `
      <div class="modal fade confirm_delete" tabindex="-1" aria-labelledby="confirm_delete_title">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h3 class="modal-title" id="confirm_delete_title">${title}</h3>
              <!--button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="${close_text}"></button-->
            </div>
            <div class="content modal-body">
              ${message}
            </div>
            <div class="actions modal-footer"></div>
          </div>
        </div>
      </div>
    `;
    let delete_btn = document.createElement("BUTTON");
    delete_btn.setAttribute("class", "delete btn btn-danger");
    delete_btn.innerHTML = delete_text ? delete_text : gettext("Delete");

    delete_btn.addEventListener("click", (e) => {
      e.preventDefault();
      document
        .querySelector("#custom_element_confirm_modal .confirm_delete")
        .classList.remove("show");
      // Delete comment
      delete_comment(ACTION_COMMENT.comment_to_delete);
      ACTION_COMMENT.comment_to_delete = null;
    });
    let cancel_btn = document.createElement("BUTTON");
    cancel_btn.setAttribute("class", "cancel btn btn-secondary");
    cancel_btn.innerHTML = cancel_text ? cancel_text : gettext("Cancel");
    cancel_btn.addEventListener("click", (e) => {
      e.preventDefault();
      closeModal();
    });
    document.addEventListener("keydown", function (event) {
      if (event.key == "Escape") {
        closeModal();
      }
    })
    this.innerHTML = modal;
    this.querySelector(".actions").appendChild(delete_btn);
    this.querySelector(".actions").appendChild(cancel_btn);

    /**
     * Closes the custom confirmation modal.
     */
    function closeModal() {
      document
        .querySelector("#custom_element_confirm_modal .confirm_delete")
        .classList.remove("show");
      ACTION_COMMENT.comment_to_delete = null;
    }
  }
}
customElements.define("confirm-modal", ConfirmModal);

class CommentSince extends HTMLElement {
  constructor(since) {
    super();
    since = this.getAttribute("since") ? this.getAttribute("since") : since;
    since = typeof since === "string" ? new Date(since) : since;
    this.setAttribute("title", since.toLocaleString());
    let date_since = dayjs(since).fromNow();
    let div = document.createElement("DIV");
    div.setAttribute("class", "comment_since");
    div.innerText = date_since;
    this.appendChild(div);
    window.setInterval(() => {
      date_since = dayjs(since).fromNow();
      div.innerText = date_since;
    }, 60000);
  }
}
customElements.define("comment-since", CommentSince);
class Comment extends HTMLElement {
  constructor(
    owner,
    content,
    likes,
    added_since,
    id,
    is_parent = null,
    is_comment_owner = false,
  ) {
    super();
    this.setAttribute("class", "comment_element");
    this.setAttribute("id", id);
    let comment = document.createElement("DIV");
    comment.setAttribute("class", "comment");
    let comment_container = document.createElement("DIV");
    comment_container.setAttribute("class", "comment_container");
    let comment_content = document.createElement("div");
    comment_content.setAttribute("class", "comment_content");
    comment_content.innerHTML = `
      <div class="comment_content_header inline_flex_space">
    <h3 class="user_name">${owner}</h3>
    <comment-since since=${added_since.toISOString()}></comment-since>
      </div>
      <div class="comment_content_body">
      </div>
      <div class="comment_content_footer">
    <div class="actions inline_flex_space"></div>
    <div class="form" data-comment="${id}"></div>
      </div>
  `;
    comment_container.appendChild(comment_content);
    if (is_parent)
      comment_container.querySelector(".comment_content_body").innerHTML =
        content;
    else
      comment_container
        .querySelector(".comment_content_body")
        .appendChild(content);
    let svg_icon = [
      `<span class="unvoted"><i class="bi bi-star"></i></span>`,
      `<span class="voted"><i class="bi bi-star-fill"></i></span>`,
    ];

    let vote_text = interpolate(
      ngettext(
        '%s <span class="d-none d-md-inline">vote</span>',
        '%s <span class="d-none d-md-inline">votes</span>',
        likes,
      ),
      [likes],
    );

    let btn_classes = "comment_actions comment_vote_action";
    let vote_action = createFooterBtnAction(
      is_authenticated ? btn_classes : btn_classes + " disabled",
      "icon comment_vote_icon",
      gettext("Agree with the comment"),
      svg_icon,
      "comment_vote_btn",
      vote_text,
      id,
      0,
    );
    if (is_authenticated) {
      vote_action.addEventListener("click", toggleVote);
      vote_action.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") {
          toggleVote();
        }
      })

      /**
       * Toggles the voting action for a comment.
       */
      function toggleVote() {
        vote_action.classList.add("voting");
        let comment_id = get_comment_attribute(document.getElementById(id));
        vote(vote_action, comment_id);
      }
    }
    comment_container
      .querySelector(".comment_content_footer .actions")
      .appendChild(vote_action);

    if (user_id && !maintenance_mode) {
      svg_icon = `<i aria-hidden="true" class="bi bi-chat"></i>`;
      let response_action = createFooterBtnAction(
        "comment_actions comment_response_action",
        "icon comment_response_icon",
        gettext("Reply to comment"),
        svg_icon,
        "comment_response_btn",
        gettext("Reply"),
        null,
        0,
      );
      response_action.addEventListener("click", function () {
        toggleReply(this)
      });
      response_action.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") {
          toggleReply(this);
        }
      });

      /**
       * Toggles the reply form for a comment.
       *
       * @param {HTMLElement} element - The element that triggered the action.
       */
      function toggleReply(element) {
        let target_node = get_node(element, "form");
        if (target_node) {
          target_node.classList.toggle("show");
          element.parentElement.nextElementSibling
            .querySelector(".new_comment")
            .focus();
        }
      }

      comment_container
        .querySelector(".comment_content_footer .actions")
        .appendChild(response_action);

      if (is_comment_owner || is_video_owner || is_superuser) {
        svg_icon = `<i aria-hidden="true" class="bi bi-trash"></i>`;
        let delete_action = createFooterBtnAction(
          "comment_actions comment_delete_action",
          "icon comment_delete_icon",
          gettext("Remove this comment"),
          svg_icon,
          "comment_delete_btn",
          gettext("Delete"),
          id,
          0,
        );
        delete_action.addEventListener("click", toggleDelete);
        delete_action.addEventListener("keydown", function (event) {
          if (event.key === "Enter" || event.key === " ") {
            toggleDelete();
          }
        });

        /**
         * Toggles the delete confirmation modal for a comment.
         */
        function toggleDelete() {
          document
            .querySelector("#custom_element_confirm_modal .confirm_delete")
            .classList.add("show");
          let el = document.getElementById(id);
          ACTION_COMMENT.comment_to_delete = el;
        }

        comment_container
          .querySelector(".comment_content_footer .actions")
          .appendChild(delete_action);
      }
      let add_comment = document.createElement("DIV");
      add_comment.setAttribute("class", "add_comment");
      add_comment.innerHTML = `
        <textarea class="new_comment form-control form-control-sm"
          name="new_comment" id="comment" rows="1"
          placeholder="${gettext("Add a public comment")}"></textarea>
        <button class="btn btn-link btn-lg send_reply disabled" role="button" title="${gettext(
        "Send",
      )}">
          <i aria-hidden="true" class="bi bi-send-fill"></i>
        </button>
      `;
      let new_comment = add_comment.querySelector(".new_comment");
      let comment_reply_btn = add_comment.querySelector(".send_reply");
      comment_reply_btn.addEventListener("click", (e) => {
        this.submit_comment_reply(new_comment, add_comment, comment_reply_btn);
      });
      new_comment.addEventListener("keyup", function (e) {
        // Enable/Disable send button
        if (
          this.value.trim().length > 0 &&
          comment_reply_btn.classList.contains("disabled")
        )
          comment_reply_btn.classList.remove("disabled");

        if (this.value.trim().length === 0)
          comment_reply_btn.classList.add("disabled");
      });
      new_comment.addEventListener("keydown", (e) => {
        if (
          (e.ctrlKey && e.keyCode === 13) ||
          (e.shiftKey && e.keyCode === 13)
        ) {
          e.preventDefault();
          new_comment.value = new_comment.value + "\r\n";
          new_comment.scrollTop = new_comment.scrollHeight;
        } else if (e.keyCode === 13) {
          this.submit_comment_reply(
            new_comment,
            add_comment,
            comment_reply_btn,
          );
        }
      });
      comment_container
        .querySelector(".comment_content_footer .form")
        .appendChild(add_comment);
    }
    if (is_parent) {
      let comment_icon_svg = `<i aria-hidden="true" class="bi bi-chat-right-dots"></i>`;
      let comment_icon = document.createElement("DIV");
      comment_icon.innerHTML = comment_icon_svg;
      comment_icon.setAttribute("class", "icon comments_icon");
      let children_container = document.createElement("DIV");
      children_container.setAttribute("class", "comments_children_container");
      comment_container.appendChild(children_container);
      comment.appendChild(comment_icon);
      comment.appendChild(comment_container);
      this.appendChild(comment);
    } else {
      let comment_icon_svg = `<svg aria-hidden="true" focusable="false" data-prefix="fab" data-icon="replyd" class="svg-inline--fa fa-replyd fa-w-14" role="img" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><path fill="currentColor" d="M320 480H128C57.6 480 0 422.4 0 352V160C0 89.6 57.6 32 128 32h192c70.4 0 128 57.6 128 128v192c0 70.4-57.6 128-128 128zM193.4 273.2c-6.1-2-11.6-3.1-16.4-3.1-7.2 0-13.5 1.9-18.9 5.6-5.4 3.7-9.6 9-12.8 15.8h-1.1l-4.2-18.3h-28v138.9h36.1v-89.7c1.5-5.4 4.4-9.8 8.7-13.2 4.3-3.4 9.8-5.1 16.2-5.1 4.6 0 9.8 1 15.6 3.1l4.8-34zm115.2 103.4c-3.2 2.4-7.7 4.8-13.7 7.1-6 2.3-12.8 3.5-20.4 3.5-12.2 0-21.1-3-26.5-8.9-5.5-5.9-8.5-14.7-9-26.4h83.3c.9-4.8 1.6-9.4 2.1-13.9.5-4.4.7-8.6.7-12.5 0-10.7-1.6-19.7-4.7-26.9-3.2-7.2-7.3-13-12.5-17.2-5.2-4.3-11.1-7.3-17.8-9.2-6.7-1.8-13.5-2.8-20.6-2.8-21.1 0-37.5 6.1-49.2 18.3s-17.5 30.5-17.5 55c0 22.8 5.2 40.7 15.6 53.7 10.4 13.1 26.8 19.6 49.2 19.6 10.7 0 20.9-1.5 30.4-4.6 9.5-3.1 17.1-6.8 22.6-11.2l-12-23.6zm-21.8-70.3c3.8 5.4 5.3 13.1 4.6 23.1h-51.7c.9-9.4 3.7-17 8.2-22.6 4.5-5.6 11.5-8.5 21-8.5 8.2-.1 14.1 2.6 17.9 8zm79.9 2.5c4.1 3.9 9.4 5.8 16.1 5.8 7 0 12.6-1.9 16.7-5.8s6.1-9.1 6.1-15.6-2-11.6-6.1-15.4c-4.1-3.8-9.6-5.7-16.7-5.7-6.7 0-12 1.9-16.1 5.7-4.1 3.8-6.1 8.9-6.1 15.4s2 11.7 6.1 15.6zm0 100.5c4.1 3.9 9.4 5.8 16.1 5.8 7 0 12.6-1.9 16.7-5.8s6.1-9.1 6.1-15.6-2-11.6-6.1-15.4c-4.1-3.8-9.6-5.7-16.7-5.7-6.7 0-12 1.9-16.1 5.7-4.1 3.8-6.1 8.9-6.1 15.4 0 6.6 2 11.7 6.1 15.6z"></path></svg>`;
      let comment_icon = document.createElement("DIV");
      comment_icon.innerHTML = comment_icon_svg;
      comment_icon.setAttribute("class", "icon comments_icon");

      // add show children button action
      comment_container.setAttribute("class", "comment_child_container");
      comment_container.prepend(comment_icon);
      comment_container
        .querySelector(".comment_content")
        .classList.add("comment_content_child");
      this.classList.add("comment_child");
      this.appendChild(comment_container);
    }
  }
  submit_comment_reply(html_field, html_container, reply_btn) {
    if (html_field.value.trim() !== "") {
      // Remove focus from the text field
      html_field.blur();
      // Disable send button
      reply_btn.classList.add("disabled");

      let child_container = get_node(html_field, "comments_children_container");
      child_container.classList.add("show");

      let comment_parent = get_node(
        html_field,
        "comment_element",
        "comment_child",
      );
      add_child_comment(
        html_field,
        html_container,
        child_container,
        comment_parent,
      );
    }
  }
}
function createFooterBtnAction(
  classes,
  icon_classes,
  title,
  svg,
  span_classes,
  span_text,
  comment_id = null,
  tabIndex = null,
) {
  let el = document.createElement("DIV");
  if (tabIndex !== "null" && typeof tabIndex === "number" && Number.isInteger(tabIndex)) {
    el.setAttribute("tabindex", tabIndex.toString())
  }
  el.setAttribute("class", classes + " btn btn-link btn-sm");
  el.setAttribute("role", "button");
  if (comment_id) el.setAttribute("data-comment", comment_id);
  let el_icon = document.createElement("DIV");
  el_icon.setAttribute("class", icon_classes);
  el_icon.setAttribute("title", title);
  if (Array.isArray(svg)) el_icon.innerHTML = svg.join(" ");
  else el_icon.innerHTML = svg;
  let el_span = document.createElement("SPAN");
  el_span.setAttribute("class", span_classes);
  el_span.innerHTML = span_text;
  el.appendChild(el_icon);
  el.appendChild(el_span);
  return el;
}
function hide_or_add_show_children_btn(parent_comment, parent_id, nb_child) {
  let svg_icon_show = `<i aria-hidden="true" class="comment-show bi bi-eye"></i>`;
  let svg_icon_hide = `<i aria-hidden="true" class="comment-hide bi bi-eye-slash"></i>`;
  let txt = nb_child > 1 ? answer_plural : answer_sing;
  txt = nb_child ? `${nb_child} ${txt}` : txt;
  let children_action = createFooterBtnAction(
    "comment_actions comment_show_children_action",
    "icon comment_show_children_icon",
    gettext("Show answers"),
    [svg_icon_show, svg_icon_hide],
    "comment_show_children_btn",
    txt,
    null,
    0
  );
  children_action.addEventListener("click", toggleComment);
  children_action.addEventListener("keydown", function (event) {
    if (event.key === "Enter" || event.key === " ") {
      toggleComment();
    }
  });

  /**
   * Toggles the visibility of a comment and fetches its children if needed.
   */
  function toggleComment() {
    parent_comment.classList.toggle("show");
    fetch_comment_children(parent_comment, parent_id);
  }

  let children_container = parent_comment.querySelector(
    ".comments_children_container",
  );
  if (
    !parent_comment.querySelector(".actions .comment_show_children_action") &&
    nb_child > 0
  ) {
    parent_comment
      .querySelector(".comment_content_footer .actions .comment_vote_action")
      .after(children_action);
  } else if (
    parent_comment.querySelector(".actions .comment_show_children_action") &&
    nb_child === 0
  ) {
    // remove action if exists
    parent_comment
      .querySelector(".comment_content_footer .actions")
      .removeChild(
        parent_comment.querySelector(
          ".comment_content_footer .actions .comment_show_children_action",
        ),
      );
  }
}
customElements.define("comment-element", Comment);

/*******************  Voting for a comment  ********************
 ***************************************************************/
function vote(comment_action_html, comment_id) {
  // send request to the server to check if the current user already voted
  let vote_url = base_vote_url + comment_id + "/";
  let btn = comment_action_html.querySelector(".comment_vote_btn");
  let data = new FormData();
  data.append("csrfmiddlewaretoken", Cookies.get("csrftoken"));

  fetch(vote_url, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "X-Requested-With": "XMLHttpRequest",
    },
    body: data,
  })
    .then((response) => {
      comment_action_html.classList.remove("voting");
      if (response.ok) {
        return response.json();
      } else {
        let message = gettext("Bad response from the server.");
        if (response.status == 403) {
          message = gettext("Sorry, you're not allowed to vote by now.");
        }
        throw new Error(message);
      }
    })
    .then((data) => {
      const target_comment = document.getElementById(
        comment_action_html.dataset.comment,
      );

      let action = "";
      if (data.voted === true) {
        action = "increment";
        comment_action_html.classList.add("voted");
      } else {
        action = "decrement";
        comment_action_html.classList.remove("voted");
      }
      const nb_vote = update_comment_attribute(
        target_comment,
        null,
        "nbr_vote",
        action,
      );
      btn.innerHTML = interpolate(
        ngettext(
          '%s <span class="d-none d-md-inline">vote</span>',
          '%s <span class="d-none d-md-inline">votes</span>',
          nb_vote,
        ),
        [nb_vote],
      );
    })
    .catch((error) => {
      showalert(error.message, "alert-danger");
    });
}

/**
 * Save comment into the server
 *
 * @param  {string}      content                   Comment content text.
 * @param  {HTMLElement} textarea                  Input used to send the comment
 * @param  {Date}        date                      date of the comment
 * @param  {HTMLElement} comment_html              new Element to be added to DOM
 * @param  {HTMLElement} comment_container_html    container where to add comment_html
 * @param  {[type]}      [direct_parent_id]        [description]
 * @param  {[type]}      [top_parent_comment_html] [description]
 */
function save_comment(
  content,
  textarea,
  date,
  comment_html,
  comment_container_html,
  direct_parent_id = null,
  top_parent_comment_html = null,
) {
  // Prevent input to be modified until comment is really added.
  textarea.setAttribute("readonly", true);

  // show loader
  loader.classList.add("show");

  let post_url = base_url.replace("comment", "comment/add");
  let top_parent_id = null;
  let data = new FormData();
  if (top_parent_comment_html) {
    top_parent_id = get_comment_attribute(top_parent_comment_html);
    post_url = post_url + top_parent_id + "/";
    data.append("direct_parent", direct_parent_id);
  }
  data.append("content", content);
  data.append("date_added", date.toISOString());
  data.append("csrfmiddlewaretoken", Cookies.get("csrftoken"));
  fetch(post_url, {
    method: "POST",
    body: data,
    headers: {
      "X-Requested-With": "XMLHttpRequest",
    },
  })
    .then((response) => {
      textarea.removeAttribute("readonly");
      //raw_response = response.clone();
      if (response.ok) {
        return response.json();
      } else {
        let message = gettext("Bad response from the server.");
        if (response.status == 403) {
          message = gettext("Sorry, you can't comment this video by now.");
        }
        throw new Error(message);
      }
    })
    .then((data) => {
      textarea.value = "";
      let c = {
        author_name: data.author_name,
        is_owner: true,
        content: content,
        id: data.id,
        added: date,
        parent__id: top_parent_id,
        direct_parent__id: direct_parent_id,
        nbr_vote: 0,
      };

      if (!top_parent_id) {
        c.children = [];
        c.nbr_child = 0;
        // update all_comment data
        all_comment = [...all_comment, c];
        comment_container_html.after(comment_html);
      } else {
        /* Ensure that the top parent container is shown. */
        top_parent_comment_html.classList.add("show");

        // Fetch comment's children if not already loaded
        if (
          get_comment_attribute(top_parent_comment_html, "children").length ===
          0
        )
          fetch_comment_children(top_parent_comment_html, top_parent_id, true);
        else {
          // Add comment child into the DOM
          comment_container_html.appendChild(comment_html);
          // Scroll to the comment child
          scrollToComment(comment_html);
        }
        // update local saved data (all_comment)
        all_comment = all_comment.map((comment) => {
          if (comment.id === top_parent_id) {
            comment.children = [...comment.children, c];
            comment.nbr_child += 1;
          }
          return comment;
        });
        let nbr_child = get_comment_attribute(
          top_parent_comment_html,
          "nbr_child",
        );
        hide_or_add_show_children_btn(
          top_parent_comment_html,
          top_parent_id,
          nbr_child,
        );
        update_answer_text(top_parent_comment_html, nbr_child);
      }
      set_comments_number();
    })
    .catch((error) => {
      showalert(error.message, "alert-danger");
      //console.log(raw_response.text())
    })
    .finally(() => {
      loader.classList.remove("show");
    });
}

/**
 * Delete a comment with an animation
 *
 * @param  {HTMLElement} comment     comment to be deleted
 * @param  {boolean}     [is_child]  if comment is a comment reply
 */
function deleteWithAnimation(comment, is_child = false) {
  let selector = is_child ? ".comment_child_container" : ".comment";
  comment.querySelector(selector).classList.add("onDelete");
  window.setTimeout(() => {
    comment.parentElement.removeChild(comment);
  }, 999);
}
/**
 * Delete a comment
 *
 * @param  {HTMLElement} comment  comment to be deleted
 */
function delete_comment(comment) {
  let comment_id = get_comment_attribute(comment);
  let is_child = !!get_comment_attribute(comment, "parent__id");
  let url = base_delete_url + comment_id + "/";
  let formdata = new FormData();
  formdata.append("csrfmiddlewaretoken", Cookies.get("csrftoken"));
  fetch(url, {
    method: "POST",
    body: formdata,
    headers: {
      "X-Requested-With": "XMLHttpRequest",
    },
  })
    .then((response) => {
      if (response.ok) {
        response.json().then((data) => {
          if (data.deleted) {
            showalert(
              gettext("The comment has been deleted successfully."),
              "alert-success",
            );
            let parent_el = null;
            if (is_child) {
              parent_el = get_node(comment, "comment_element", "comment_child");
              let parent_id = get_comment_attribute(parent_el);
              delete_comment_child_DOM(comment, parent_id, is_child); // delete all children from the DOM
              let remaining_children = get_comment_attribute(
                parent_el,
                "nbr_child",
              );
              deleteWithAnimation(comment, true); // delete comment from the DOM
              hide_or_add_show_children_btn(
                parent_el,
                parent_id,
                remaining_children,
              ); // Manage show answers button
              update_answer_text(parent_el, remaining_children); // Update number of child text displayed
              set_comments_number();
              return;
            }
            all_comment = all_comment.filter(
              (c) => c.id != data.comment_deleted,
            );
            deleteWithAnimation(comment, false);
            set_comments_number();
          } else showalert(data.message, "alert-warning");
        });
      } else {
        let message = gettext("Bad response from the server.");
        if (response.status == 403) {
          message = gettext("Sorry, you can't delete this comment by now.");
        }
        showalert(message, "alert-danger");
        //console.log("Bad response from network", response);
      }
    })
    .catch((error) => {
      console.log(error);
      console.log(error.message);
    });
}

/**
 * Recursive delete of a comment and its children
 *
 * @param  {HTMLElement} comment                comment to be deleted
 * @param  {string}      comment_top_parent_id  id of parent
 * @param  {boolean}     [is_child]             if comment is a comment reply
 */
function delete_comment_child_DOM(comment, comment_top_parent_id, is_child) {
  if (is_child) {
    let comment_id = get_comment_attribute(comment);
    let list_parent_id = [comment_id];

    all_comment = all_comment.map((parent_comment) => {
      if (parent_comment.id === comment_top_parent_id) {
        parent_comment.children = parent_comment.children
          .filter((child_comment) => child_comment.id !== comment_id)
          .filter((child_comment) => {
            if (list_parent_id.includes(child_comment.direct_parent__id)) {
              list_parent_id = [...list_parent_id, child_comment.id];
              // Remove comment html element from DOM
              let html_id = `#comment_${new Date(
                child_comment.added,
              ).getTime()}`;
              let child_comment_html = document.querySelector(html_id);
              deleteWithAnimation(child_comment_html, true);
            }
            return !list_parent_id.includes(child_comment.direct_parent__id); // Remove comment data from all_comment
          });
        parent_comment.nbr_child = parent_comment.children.length;
      }
      return parent_comment;
    });
  }
}

/**
 * Get Html element his position
 *
 * @param  {HTMLElement} element  element to get
 */
function getElementPosition(element) {
  let xPosition = 0;
  let yPosition = 0;
  // get body padding top if exists that will be
  let bodyPaddingTop = Number.parseInt(
    getComputedStyle(document.body)["padding-top"] ?? 0,
  );

  while (element) {
    xPosition += element.offsetLeft - element.scrollLeft + element.clientLeft;
    yPosition += element.offsetTop - element.scrollTop + element.clientTop;
    element = element.offsetParent;
  }
  // subtract the padding top from the body to the yPosition to get closer to the exact value
  return { x: xPosition, y: yPosition - bodyPaddingTop };
}

/**
 * Check if element is visible in the viewport
 *
 * @param  {HTMLElement} el  element to be checked
 */
function isInViewport(el) {
  const rect = el.getBoundingClientRect();
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <=
    (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  );
}

/**
 * Scroll to a specific comment
 *
 * @param  {HTMLElement} targetComment  target element of the scroll
 */
function scrollToComment(targetComment) {
  const alreadyInViewPort = isInViewport(targetComment);
  const animationDuration = alreadyInViewPort ? 2000 : 4000;
  if (!alreadyInViewPort) {
    let currentElementPosition = getElementPosition(targetComment);
    window.scrollTo({
      top: currentElementPosition.y,
      left: currentElementPosition.x,
      behavior: "smooth",
    });
  }
  let htmlTarget = targetComment.querySelector(".comment_content");
  if (htmlTarget.classList.contains("scroll_to"))
    htmlTarget.classList.remove("scroll_to");

  window.setTimeout(() => {
    htmlTarget.classList.remove("scroll_to");
  }, animationDuration);

  htmlTarget.classList.add("scroll_to");
}

/**
 * Add the owner of parent comment as a tag.
 *
 * @param  {string}      comment_value   text to put in the comment
 * @param  {HTMLElement} parent_comment  parent element
 */
function add_user_tag(comment_value, parent_comment) {
  const reply_to = get_comment_attribute(parent_comment, "author_name");
  const reply_content = get_comment_attribute(parent_comment, "content");
  const tag = document.createElement("a");
  tag.setAttribute("href", "#");
  tag.setAttribute("class", "reply_to btn-link");
  tag.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    scrollToComment(parent_comment);
  });
  tag.innerHTML = `
    <i aria-hidden="true" class="bi bi-reply-fill"></i>
    <span class="reply_author">@${reply_to}</span>
    <span class="reply_content">${reply_content}</span>`;
  const comment_text = document.createElement("span");
  comment_text.setAttribute("class", "comment_text");
  comment_text.innerText = comment_value;

  const comment_content = document.createElement("p");
  comment_content.appendChild(tag);
  comment_content.appendChild(comment_text);
  return comment_content;
}

/**
 * return color index.
 *
 * @param  {HTMLElement} comment         target comment
 * @param  {HTMLElement} parent_comment  parent element
 */
function setBorderLeftColor(comment, parent_element) {
  try {
    let index = Number.parseInt(parent_element.dataset.level) + 1;
    if (index >= COLORS.length) {
      comment.dataset.level = COLORS.length - 1;
      comment.querySelector(".comment_content").style.borderLeft = `4px solid ${COLORS[COLORS.length - 1]
        }`;
      comment.querySelector(".comments_icon").style.color = `${COLORS[COLORS.length - 1]
        }`;
    } else {
      comment.dataset.level = index;
      comment.querySelector(
        ".comment_content",
      ).style.borderLeft = `4px solid ${COLORS[index]}`;
      comment.querySelector(".comments_icon").style.color = `${COLORS[index]}`;
    }
  } catch (e) {
    comment.dataset.level = COLORS.length - 1;
    comment.querySelector(".comment_content").style.borderLeft = `4px solid ${COLORS[COLORS.length - 1]
      }`;
    comment.querySelector(".comments_icon").style.color = `${COLORS[COLORS.length - 1]
      }`;
  }
}

/****************  Add parent Comment  ****************
 ******************************************************/
if (is_authenticated) {
  let add_parent_comment = document.querySelector("form.add_parent_comment");
  add_parent_comment.addEventListener("submit", (e) => {
    e.preventDefault();
    let date_added = new Date();
    let el = add_parent_comment.querySelector(".new_parent_comment");
    if (el.value.trim() != "") {
      let comment_content = el.value;
      let c = new Comment(
        user_fullName,
        comment_content,
        0,
        date_added,
        `comment_${date_added.getTime()}`,
        true,
        true,
      );
      c.dataset.level = "-1";
      // INSERT INTO DATABASE THE CURRENT COMMENT CHILD
      save_comment(
        comment_content,
        el,
        date_added,
        c,
        document.querySelector(
          ".comment_container .comment_content form.add_parent_comment",
        ),
      );
    }
  });
}

/**
 * Fetch children and add them into the DOM.
 *
 * @param  {HTMLElement} parent_comment_html
 * @param  {string}      parent_comment_id
 * @param  {boolean}     scroll_to_last
 */
function fetch_comment_children(
  parent_comment_html,
  parent_comment_id,
  scroll_to_last = false,
) {
  // fetch children only once
  if (
    all_comment.find((c) => c.id === parent_comment_id).children.length === 0
  ) {
    loader.classList.add("show"); // waiting for charging children

    let url = base_url.replace("/comment/", `/comment/${parent_comment_id}/`);
    fetch(url).then((response) => {
      response.json().then((data) => {
        // Saving children in all_comment
        all_comment = all_comment.map((parent_comment) => {
          if (parent_comment.id === parent_comment_id) {
            parent_comment.children = data.children;
            // Update DOM with children comments
            parent_comment.children.forEach((comment_child, index) => {
              let parent_to_scroll = parent_comment_html;
              if (
                comment_child.direct_parent__id != null &&
                comment_child.direct_parent__id !== comment_child.parent__id
              ) {
                let direct_parent_comment = parent_comment.children.find(
                  (c_obj) => c_obj.id === comment_child.direct_parent__id,
                );
                let direct_parent_html_id = `comment_${new Date(
                  direct_parent_comment.added,
                )
                  .getTime()
                  .toString()}`;
                parent_to_scroll = parent_comment_html.querySelector(
                  `#${direct_parent_html_id}`,
                );
              }

              let date_added = new Date(comment_child.added);

              let comment_child_content = add_user_tag(
                comment_child.content,
                parent_to_scroll,
                parent_comment.author_name,
              );

              let comment_child_html = new Comment(
                `${comment_child.author_name}`,
                comment_child_content,
                comment_child.nbr_vote,
                date_added,
                `comment_${date_added.getTime()}`,
                false,
                comment_child.is_owner,
              );

              parent_comment_html
                .querySelector(".comments_children_container")
                .appendChild(comment_child_html);
              setBorderLeftColor(comment_child_html, parent_to_scroll);
              manage_vote_frontend(comment_child.id, comment_child_html);

              // Scrolling to the last comment child added
              if (
                scroll_to_last &&
                index === parent_comment.children.length - 1
              )
                scrollToComment(comment_child_html);
            });
          }
          loader.classList.remove("show");
          return parent_comment;
        });
      });
    });
  }
}

/**
 * Add child Comment.
 *
 * @param  {HTMLElement} el                      input/textarea element containing the comment
 * @param  {HTMLElement} el_container            parent containing the input (usually div.add_comment)
 * @param  {HTMLElement} child_container         container where to add the comment
 * @param  {HTMLElement} top_parent_comment_html
 */
function add_child_comment(
  el,
  el_container,
  child_container,
  top_parent_comment_html,
) {
  let date_added = new Date();
  if (el.value.trim() !== "") {
    let child_direct_parent = document.querySelector(
      `#${el.parentElement.parentElement.dataset.comment}`,
    );

    let comment_child_content = add_user_tag(el.value, child_direct_parent);
    let c = new Comment(
      user_fullName,
      comment_child_content,
      0,
      date_added,
      `comment_${date_added.getTime()}`,
      false,
      true,
    );
    setBorderLeftColor(c, child_direct_parent);
    // INSERT INTO DATABASE THE CURRENT COMMENT CHILD
    let direct_parent_id = get_comment_attribute(child_direct_parent);

    save_comment(
      el.value,
      el,
      date_added,
      c,
      child_container,
      direct_parent_id,
      top_parent_comment_html,
    );

    el_container.parentElement.classList.remove("show");
  }
}

/**
 * Set comment backend attribute from saved data.
 *
 * @param {HTMLElement} comment_html
 * @param {any}         value
 * @param {string}      attr
 * @param {string}      [action]       values(increment or decrement)
 * @return {any}
 */
function update_comment_attribute(comment_html, value, attr, action = null) {
  let curr_html_id = comment_html.getAttribute("id");
  let new_value = value;
  all_comment = all_comment.map((comment_data) => {
    let comment_htmlID = `comment_${new Date(comment_data.added).getTime()}`;
    if (comment_htmlID == curr_html_id) {
      if (action !== null && action === "increment") {
        comment_data[attr] += 1;
        new_value = comment_data[attr];
      } else if (action !== null && action === "decrement") {
        comment_data[attr] -= 1;
        new_value = comment_data[attr];
      } else comment_data[attr] = value;
    }
    comment_data.children = comment_data.children.map((child_comment_data) => {
      comment_htmlID = `comment_${new Date(
        child_comment_data.added,
      ).getTime()}`;
      if (comment_htmlID == curr_html_id) {
        if (action !== null && action === "increment") {
          child_comment_data[attr] += 1;
          new_value = child_comment_data[attr];
        } else if (action !== null && action === "decrement") {
          child_comment_data[attr] -= 1;
          new_value = child_comment_data[attr];
        } else child_comment_data[attr] = value;
      }
      return child_comment_data;
    });
    return comment_data;
  });
  return new_value;
}

/**
 * Return comment backend attribute from saved data.
 *
 * @param  {HTMLElement} comment_html
 * @param  {string}      [attr]        requested attribute
 */
function get_comment_attribute(comment_html, attr = "id") {
  let curr_html_id = comment_html.getAttribute("id");
  let comment_attr = null;
  for (const comment_data of all_comment) {
    let comment_htmlID = `comment_${new Date(comment_data.added).getTime()}`;
    if (comment_htmlID == curr_html_id) {
      comment_attr = comment_data[attr];
      break;
    }
    for (const child_comment_data of comment_data.children) {
      comment_htmlID = `comment_${new Date(
        child_comment_data.added,
      ).getTime()}`;
      if (comment_htmlID == curr_html_id) {
        comment_attr = child_comment_data[attr];
        break;
      }
    }
    if (comment_attr) return comment_attr;
  }
  return comment_attr;
}

/**
 * html Contains all Classes ?
 *
 * @param  {HTMLElement} html_el
 * @param  {Array}       classes
 * @return {boolean}     true if html_el contains all classes
 */
function htmlContainsClass(html_el, classes) {
  let ctn = true;
  classes.split(".").forEach((cls) => {
    if (!html_el.classList.contains(cls)) ctn = false;
  });
  return ctn;
}

/**
 * Get parentNode or sibling node.
 *
 * @param  {HTMLElement} el
 * @param  {string}      class_name
 * @param  {string}      not
 * @return {HTMLElement} parentNode or sibling node
 */
function get_node(el, class_name, not) {
  class_name = class_name || "comment_container";
  not = not || "";
  let selector = !!not ? `.${class_name}:not(.${not})` : `.${class_name}`;
  let foundedElement = el.querySelector(selector);
  if (htmlContainsClass(el, class_name) && !htmlContainsClass(el, not)) {
    return el;
  }
  if (foundedElement) {
    return foundedElement;
  } else {
    return get_node(el.parentElement, class_name, not);
  }
}

/**
 * Manage hide/show child comment text
 * update the number of child comments displayed
 * only if element exists
 *
 * @param  {HTMLElement} el
 * @param  {number}      [nb_child]
 */
function update_answer_text(el, nb_child = 0) {
  let children_container = get_node(el, "comments_children_container");
  nb_child = nb_child === 0 ? "" : nb_child;
  let txt = nb_child > 1 ? answer_plural : answer_sing;
  txt = `${nb_child} ${txt}`;
  let answer_text_element = el.querySelector(".comment_show_children_btn");
  if (answer_text_element) answer_text_element.innerText = txt;
}

/**
 * Manage vote icons
 *
 * @param  {string}  id
 * @param  {HTMLElement} el
 */
function manage_vote_frontend(id, el) {
  VOTED_COMMENTS.forEach((obj) => {
    if (obj.comment__id === id) {
      el.querySelector(".comment_vote_action").classList.add("voted");
    }
  });
}

/**
 * Set number comments in comment label
 */
function set_comments_number() {
  let nb_comments =
    all_comment.reduce((acc, curr) => (acc += curr.nbr_child), 0) +
    all_comment.length;
  comment_title.innerText = interpolate(
    ngettext("%s comment", "%s comments", nb_comments),
    [nb_comments],
  );
}

/************  Get vote from the server  **************
 ******************************************************/
loader.classList.add("show");
fetch(base_vote_url)
  .then((response) => {
    response.json().then((data) => {
      VOTED_COMMENTS = data.comments_votes;
    });
  })
  .finally(function () {
    /************  Get data from the server  **************
     ******************************************************/
    let url = `${base_url}?only=parents`;
    fetch(url).then((response) => {
      response.json().then((data) => {
        all_comment = [];
        data.forEach((comment_data) => {
          comment_data.children = []; // init children to empty array
          all_comment = [...all_comment, comment_data]; // updating all_comment
          let parent_container = document.querySelector(
            ".comment_container .comment_content",
          );
          let date_added = new Date(comment_data.added);
          let html_id = `comment_${date_added.getTime().toString()}`;
          let parent_c = new Comment(
            `${comment_data.author_name}`,
            comment_data.content,
            comment_data.nbr_vote,
            date_added,
            html_id,
            true,
            comment_data.is_owner,
          );
          parent_c.dataset.level = "-1";
          manage_vote_frontend(comment_data.id, parent_c);
          if (is_authenticated)
            parent_container
              .querySelector("form.add_parent_comment")
              .after(parent_c);
          else
            parent_container
              .querySelector(".comment_counter_container")
              .after(parent_c);
          hide_or_add_show_children_btn(
            parent_c,
            comment_data.id,
            comment_data.nbr_child,
          );
        });
        set_comments_number(); // update number of comments from comment label
      });
    });
    loader.classList.remove("show");
  });
