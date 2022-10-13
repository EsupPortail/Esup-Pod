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

//chech if user

class InfiniteLoader {
  constructor(url, onBeforePageLoad, onAfterPageLoad) {
    this.infinite_loading = document.querySelector(".infinite-loading");
    this.videos_list = document.getElementById("videos_list");
    this.page = 1;
    this.onBeforePageLoad = onBeforePageLoad;
    this.onAfterPageLoad = onAfterPageLoad;
    this.url = url;
    window.addEventListener("load", (e) => {
      this.initMore();
    });
    window.addEventListener("scroll", (e) => {
      this.initMore();
    });
  }

  initMore() {
    if (isFooterInView()) {
      let url = this.url;
      this.onBeforePageLoad();
      this.getData(url, this.page);
      console.log("page", this.page);
      this.page += 1;
    }
  }

  getData(url, page) {
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
          .firstChild;
        let element = this.videos_list;
        html.childNodes.forEach(function (node) {
          element.appendChild(node);
        });
        this.onAfterPageLoad();
      })
      .catch((error) => {
        console.log(error);
      });
  }
}
