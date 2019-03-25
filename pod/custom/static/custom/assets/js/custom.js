$(function()
{
  $(".navbar-brand strong").remove();
  $( ".nav-search #s" ).focus( e => {
      console.log($(this).parent());
  })
});
