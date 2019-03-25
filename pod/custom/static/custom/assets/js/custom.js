$(function()
{
  $(".navbar-brand strong").remove();
  $( "#s" ).focus( e => {
      $(this).parent().css({position: fixed});
  })
});
