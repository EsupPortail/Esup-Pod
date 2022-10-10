class Waypoint {
  constructor(
    waypointElement,
    handler,
    onBeforeLoadCallback,
    onAfterLoadCallback
  ) {
    this.waypointElement = waypointElement;
    this.handler = handler;
    this.onBeforeLoadCallback = onBeforeLoadCallback;
    this.onAfterLoadCallback = onAfterLoadCallback;
    this.initWaypoint();
  }

  initWaypoint() {
    window.addEventListener(
      "scroll",
      function (event) {
        if (this.onBeforeLoadCallback) {
          if (isInViewport(theElementToWatch)) {
            this.onBeforeLoadCallback();
            this.handler();
          } else {
            this.handler();
          }
        }
      },
      false
    );
  }
  isInViewPort() {
    // Get the bounding client rectangle position in the viewport
    var bounding = this.waypointElement.getBoundingClientRect();

    // Checking part. Here the code checks if it's *fully* visible
    // Edit this part if you just want a partial visibility
    if (
      bounding.top >= 0 &&
      bounding.left >= 0 &&
      bounding.right <=
        (window.innerWidth || document.documentElement.clientWidth) &&
      bounding.bottom <=
        (window.innerHeight || document.documentElement.clientHeight)
    ) {
      return true;
    } else {
      return false;
    }
  }

  onBeforePageLoad() {
    if (this.onBeforeLoadCallback) {
      this.onBeforeLoadCallback();
    }
  }
}
