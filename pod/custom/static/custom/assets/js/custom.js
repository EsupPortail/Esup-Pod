$(function()
{
  $(".navbar-brand strong").remove();
  $( "#s" ).focus( e => {
      $("form#nav-search").addClass("staticposition");
  })
  $( "#s" ).blur( e => {
      $("form#nav-search").removeClass("staticposition");
  })

  let screenWidth = $(window).width();
  let MIN_WIDTH = 767;
  let btnConnexion = $(".btn.btn-connexion");
  let btnConnexionlogo = $(".btn-custom.logo");

  let displayConnexionLogo = function()
  {
      if( screenWidth <= MIN_WIDTH  )
      {
        if( btnConnexion.is(":visible") )
        {
          btnConnexion.addClass('hide-custom');
        }
        if( btnConnexionlogo.is(":hidden") )
        {
          btnConnexionlogo.removeClass('hide-custom');
        }

      }
      else
      {
        if( btnConnexionlogo.is(":visible") )
        {
          btnConnexionlogo.addClass('hide-custom');
        }
        if( btnConnexion.is(":hidden") )
        {
          btnConnexion.removeClass("hide-custom");
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
