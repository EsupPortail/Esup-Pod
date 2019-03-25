$(function()
{
  $(".navbar-brand strong").remove();
  $( "#s" ).focus( e => {
      $("form#nav-search").addClass("staticposition");
  })
  $( "#s" ).blur( e => {
      $("form#nav-search").removeClass("staticposition");
  })
});
