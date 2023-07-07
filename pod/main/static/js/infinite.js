// this function (isFooterInView) is not used elsewhere
/*
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
*/
/* Another way to detect the footer
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
*/

const isElementXPercentInViewport = function () {
  percentVisible = 95;
  var footer = document.querySelector(
    "footer.container-fluid.pod-footer-container",
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
  constructor(
    url,
    callBackBeforeLoad,
    callBackAfterLoad,
    nextPage = true,
    page = 2,
  ) {
    this.infinite_loading = document.querySelector(".infinite-loading");
    this.videos_list = document.getElementById("videos_list");
    this.next_page_number = page;
    this.current_page_number = page - 1;
    this.nextPage = nextPage;
    this.callBackBeforeLoad = callBackBeforeLoad;
    this.callBackAfterLoad = callBackAfterLoad;
    this.url = url;
    this.scroller_init = (e) => {
      if (document.body.getBoundingClientRect().top > this.scrollPos) {
      } else {
        if (isElementXPercentInViewport()) {
          if (
            this.nextPage &&
            this.next_page_number > this.current_page_number
          ) {
            this.current_page_number = this.next_page_number;
            this.initMore();
          }
        }
      }
      this.scrollPos = document.body.getBoundingClientRect().top;
    };
    window.addEventListener("scroll", this.scroller_init);
  }
  async initMore() {
    this.callBackBeforeLoad();
    let url = this.url;
    this.getData(url, this.next_page_number, this.nextPage).then((data) => {
      if (data !== null && data !== undefined) {
        const html = new DOMParser().parseFromString(data, "text/html");
        /*if (html.getElementById("videos_list").dataset.nextpage !== "True") {
          this.nextPage = false;
        }*/
        // data-nextpage="{{ videos.has_next|yesno:'true,false' }}"
        this.nextPage = html.getElementById("videos_list").dataset.nextpage;
        let element = this.videos_list;

        element.innerHTML += html.getElementById("videos_list").innerHTML;
        this.next_page_number += 1;
      }
      this.callBackAfterLoad();
    });
  }

  removeLoader() {
    window.removeEventListener("scroll", this.scroller_init);
  }

  async getData(url, page, nextPage) {
    if (!url) return;
    if (nextPage == "false") return;
    url = url + page;
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "X-CSRFToken": "{{ csrf_token }}",
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "same-origin",
    });
    const data = await response.text();
    return data;
  }
}
