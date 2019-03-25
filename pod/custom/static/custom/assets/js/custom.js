console.log($);

$(function()
{
  // Footer position absolute on authentcate view
  let screenWidth = window.screen.width;
  let MIN_WIDTH = 767;
  let pathnameExpected = "/authentication_login_gateway/";
  let currentPath = window.location.pathname;

  $( window ).resize( e =>
  {
    screenWidth = $( window ).width();
    if( screenWidth > MIN_WIDTH && currentPath == pathnameExpected && !$( "footer" ).hasClass( "fixebottom" ) )
    {
      $( "footer" ).addClass( "fixebottom" );
    }
    else if( $( "footer" ).hasClass( "fixebottom" ) )
    {
      $( "footer" ).removeClass( "fixebottom" );
    }

  })


});
