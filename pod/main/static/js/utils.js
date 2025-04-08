/**
 * Esup-Pod Main utilities
 */

// Read-only globals defined in jQuery
/*
global $
*/

function Utils() {}

Utils.prototype = {
  constructor: Utils,
  /**
   * Check if element is partial/fully in screen view
   * @param {HTMLElement} element - element to check
   * @param {Boolean} fullyInView - check full in view
   **/
  isElementInView: function (element, fullyInView) {
    const pageTop = $(window).scrollTop();
    const pageBottom = pageTop + $(window).height();
    const elementTop = element.offsetTop; //$(element).offsetTop;
    const elementBottom = elementTop + $(element).height();

    if (fullyInView === true)
      return pageTop < elementTop && pageBottom > elementBottom;
    return elementTop <= pageBottom && elementBottom >= pageTop;
  },
};
export const Helper = new Utils();
