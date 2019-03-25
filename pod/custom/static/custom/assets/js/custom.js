console.log($);

$(function()
{
  // Footer position absolute on authentcate view
  let screenWidth = window.screen.width;
  let MIN_WIDTH = 767;
  let pathnameExpected = "/authentication_login_gateway/";
  let currentPath = window.location.pathname;
  let fixeFooter = function(){
    if( currentPath === pathnameExpected )
    {
      if( screenWidth > MIN_WIDTH  )
      {
        if( !($( "footer" ).hasClass( "fixebottom" ))  )
        {
          $( "footer" ).addClass( "fixebottom" );
          return;
        }
      }
    }
    $( "footer" ).removeClass( "fixebottom" );

  }
  fixeFooter()
  $( window ).resize( e =>
  {
    screenWidth = $( window ).width();
    fixeFooter()
  })


  // VIEW VIDEOS REMOVE FOOTER HEIGHT 80px
  $( "footer" ).css("height", "auto !important");
});
