console.log($);

$(function()
{
  // Footer position absolute on authentcate view
  let screenWidth = window.screen.width;
  let MIN_WIDTH = 767;
  let pathnameExpected = "/authentication_login_gateway/";
  let currentPath = window.location.pathname;

  $( window ).on("resize", e =>
  {
    console.log(window.screen.width);
  })

  if( screenWidth > MIN_WIDTH && currentPath == pathnameExpected )
  {
    $('footer').addClass('fixebottom');
  }
  else {
    $('footer').removeClass('fixebottom');
  }

});
