$(function()
{
  $(".navbar-brand strong").remove();
  $( "#s" ).focus( e => {
      $("form#nav-search").addClass("staticposition");
  })
  $( "#s" ).blur( e => {
      $("form#nav-search").removeClass("staticposition");
  })

  let screenWidth = window.width;
  let MIN_WIDTH = 767;
  let btnConnexion = $(".btn.btn-connexion");
  let btnConnexionlogo = $(".btn-custom.logo");

  let displayConnexionLogo = function()
  {
      if( screenWidth <= MIN_WIDTH  )
      {
        if( btnConnexion.is(":visible") )
        {
          btnConnexion.hide();
        }
        if( btnConnexionlogo.is(":hidden") )
        {
          btnConnexionlogo.show();
        }

      }
      else
      {
        if( btnConnexionlogo.is(":visible") )
        {
          btnConnexionlogo.hide();
        }
        if( btnConnexion.is(":hidden") )
        {
          btnConnexion.show();
        }
      }
  }
  displayConnexionLogo();

  $( window ).resize( e =>
  {
    screenWidth = $( window ).width();
    displayConnexionLogo( )
  })


});
