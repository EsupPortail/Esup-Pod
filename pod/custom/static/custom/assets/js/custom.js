console.log($);

$(function()
{
  // Footer position absolute on authentcate view
  let screenWidth = window.screen.width;
  let MIN_WIDTH = 767;
  let pathnameExpected = "/authentication_login_gateway/";
  let currentPath = window.location.pathname;

  let fixeFooter = function(){
    if( screenWidth > MIN_WIDTH && currentPath == pathnameExpected )
    {
      if( !($( "footer" ).hasClass( "fixebottom" ))  )
      {
        $( "footer" ).addClass( "fixebottom" );
      }
    }
    else
    {
      $( "footer" ).removeClass( "fixebottom" );
    }
  }
  fixeFooter()
  $( window ).resize( e =>
  {
    screenWidth = $( window ).width();
    fixeFooter()
  })
});
