function isFooterInView() {
  var footer = document.querySelector(
    "footer.container-fluid.pod-footer-container"
  );
  var rect = footer.getBoundingClientRect();
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <=
      (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  );
}
function detect_visibility() {
  var element = document.querySelector(
    "footer.container-fluid.pod-footer-container"
  );

  var top_of_element = element.offsetTop;
  var bottom_of_element =
    element.offsetTop + element.offsetHeight + element.style.marginTop;
  var bottom_of_screen = window.scrollY + window.innerHeight;
  var top_of_screen = window.scrollY;

  if (bottom_of_screen > top_of_element && top_of_screen < bottom_of_element) {
    // Element is visible write your codes here
    // You can add animation or other codes here
    return true;
  } else {
    // the element is not visible, do something else
    return false;
  }
}

const isElementXPercentInViewport = function () {
  percentVisible = 95;
  var footer = document.querySelector(
    "footer.container-fluid.pod-footer-container"
  );
  let rect = footer.getBoundingClientRect(),
    windowHeight = window.innerHeight || document.documentElement.clientHeight;

  return !(
    Math.floor(100 - ((rect.top >= 0 ? 0 : rect.top) / +-rect.height) * 100) <
      percentVisible ||
    Math.floor(100 - ((rect.bottom - windowHeight) / rect.height) * 100) <
      percentVisible
  );
};

class InfiniteLoader {
  constructor(url, callBackBeforeLoad, callBackAfterLoad, nextPage = true) {
    this.infinite_loading = document.querySelector(".infinite-loading");
    this.videos_list = document.getElementById("videos_list");
    this.page = 0;
  
    this.nextPage = nextPage;
    this.callBackBeforeLoad = callBackBeforeLoad;
    this.callBackAfterLoad = callBackAfterLoad;
    this.url = url;
    window.addEventListener("scroll", (e) => {
      if (document.body.getBoundingClientRect().top > this.scrollPos) {
      } else {
        if (isElementXPercentInViewport()) {
          console.log(this.nextPage)
          if (this.nextPage) 
            this.initMore();
        }
      }
      this.scrollPos = document.body.getBoundingClientRect().top;
    });
  }

  initMore() {
    let url = this.url;
    this.callBackBeforeLoad();
    this.page += 1;
    this.getData(url, this.page);
    
  }

  getData(url, page) {
    if (!url) return;
    url = url + page;
    fetch(url, {
      method: "GET",
      headers: {
        "X-CSRFToken": "{{ csrf_token }}",
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "same-origin",
    })
      .then((response) => response.text())
      .then((data) => {
        // parse data into html

        let html = new DOMParser().parseFromString(data, "text/html").body.firstChild;
      
        if (html.getAttribute("nextPage") != "True") {
          this.nextPage = false ;
        }
        
        let element = this.videos_list;
        
        html.childNodes.forEach(function (node) {
          element.appendChild(node);
        });
        this.callBackAfterLoad();
      })
      .catch((error) => {
        console.log(error);
      });
  }
}
