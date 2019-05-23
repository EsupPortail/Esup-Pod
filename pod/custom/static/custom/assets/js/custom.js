$(function()
{
  $(document).ready(function(){
    
	  
    var pathname = window.location.pathname
    views = ["/authentication_login_gateway/", "/accounts/login/"]
    var footer = $("footer.text-muted.bg-dark.pt-2") || $('footer.text-muted') || $('footer')
    let screenWidth = $( window ).width();
    let MIN_WIDTH = 767;

    if( views.includes(pathname) )
    {

      let fixeFooter = function()
      {
        if( screenWidth > MIN_WIDTH  )
        {
          if( !( footer.hasClass( "fixebottom" ) )  )
          {
            footer.addClass( "fixebottom" );
          }
        }
        else
        {
          footer.removeClass( "fixebottom" );
        }
      }
      fixeFooter( )
      $( window ).resize( e =>
      {
        screenWidth = $( window ).width();
        fixeFooter( )
      })

      if( views.includes(pathname) )
      {
        footer.addClass('fixebottom')
      }
      else
      {
        footer.removeClass('fixebottom')
      }
    }	
  });

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
