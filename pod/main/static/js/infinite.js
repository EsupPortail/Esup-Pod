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
/*
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

*/

//chech if user

class InfiniteLoader {
  constructor(url, callBackBeforeLoad, callBackAfterLoad) {
    this.infinite_loading = document.querySelector(".infinite-loading");
    this.videos_list = document.getElementById("videos_list");
    this.page = 1;
    this.callBackBeforeLoad = callBackBeforeLoad;
    this.callBackAfterLoad = callBackAfterLoad;
    this.url = url;
   
    window.addEventListener("scroll", (e) => {
      this.initMore();
    });
  }

  initMore() {
    console.log(isFooterInView())
    if (isFooterInView()) {
      let url = this.url;
      this.callBackBeforeLoad();
      this.getData(url, this.page);
      console.log("page", this.page);
      this.page += 1;
    }
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

        let html = new DOMParser().parseFromString(data, "text/html").body
        let element = this.videos_list.parentNode;
        html.childNodes.forEach(function (node) {
          console.log(node)
          element.appendChild(node);
        });
        this.callBackAfterLoad();
      })
      .catch((error) => {
        console.log(error);
      });
  }
}
