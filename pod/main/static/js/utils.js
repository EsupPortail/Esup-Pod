function Utils() {}

Utils.prototype = {
  constructor: Utils,
  /**
   * Check if element is partial/fully in screen view
   * @param element {HTMLElement} element to check
   * @param fullyInView {Boolean} check full in view
   **/
  isElementInView: function (element, fullyInView) {
    const pageTop = $(window).scrollTop();
    const pageBottom = pageTop + $(window).height();
    const elementTop = $(element).offset().top;
    const elementBottom = elementTop + $(element).height();

    if (fullyInView === true)
      return pageTop < elementTop && pageBottom > elementBottom;
    return elementTop <= pageBottom && elementBottom >= pageTop;
  },
};
export const Helper = new Utils();
