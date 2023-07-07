/**
 *  Javascript for Esup-Portal video_edit form
 **/
document.addEventListener(
  "DOMContentLoaded",
  function () {
    // Display type description as field help when changed
    const target = "id_type";
    // Cannot be used in django admin pages, as <div class="help"> has no id.
    const helpContainer = document.getElementById(target + "Help");
    const selector = document.getElementById(target);
    display_option_desc(selector, helpContainer);
    selector.addEventListener("change", function () {
      display_option_desc(this, helpContainer);
    });
  },
  false,
);

function display_option_desc(selectBox, container) {
  // Display in $container the title of current $selectedBox option.
  var target_title =
    selectBox.options[selectBox.selectedIndex].getAttribute("title");
  if (!target_title) {
    target_title = gettext("Select the general type of the video.");
  }
  container.innerHTML = target_title;
}
