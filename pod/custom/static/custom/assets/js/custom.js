$(function()
{
  $(".navbar-brand strong").remove();
  $( "#s" ).focus( e => {
      $(this).parent().addClass("staticposition");
  })
  $( "#s" ).blur( e => {
      $(this).parent().removeClass("staticposition");
  })
});
