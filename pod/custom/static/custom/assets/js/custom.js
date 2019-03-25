$(function()
{
  $(".navbar-brand strong").remove();
  $( "#s" ).focus( e => {
      console.log($(this).parent());
  })
});
