/**
 *  Javascript for Esup-Portal video_edit form
 **/
(function () {
  // Display type description as field help when changed
  const target = "id_type";
  const helpContainer = document.getElementById(target + "Help");
  const select = document.getElementById(target)
  display_option_desc(select, helpContainer);
  select.addEventListener("change", function() {
    display_option_desc(this, helpContainer);
  });

})();

function display_option_desc(selectBox, container){
  // Display in $container the title of current $selectedBox option.
  var target_title = selectBox.options[selectBox.selectedIndex].getAttribute("title");
  if (!target_title) {
    target_title = gettext("Select the general type of the video.");
  }
  container.innerHTML = target_title;
}