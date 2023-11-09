/**
 * @file Esup-Pod functions for displaying channels dynamically.
 */

// Read-only globals defined in base.html
/*
  global GET_CHANNELS_FOR_SPECIFIC_CHANNEL_TAB_REQUEST_URL, GET_CHANNEL_TAGS_REQUEST_URL,
  GET_THEMES_FOR_SPECIFIC_CHANNEL_REQUEST_URL
*/


/**
 * Set attributes of an HTML element with a two-dimensional array.
 *
 * @param {HTMLElement} htmlElement The HTML element.
 * @param {string[][]} attributeCouples The two-dimensional array.
 */
function setAttributesWithTab(htmlElement, attributeCouples) {
  attributeCouples.forEach((attributeCouple) => {
    htmlElement.setAttribute(attributeCouple[0], attributeCouple[1]);
  });
}

/**
 * Get the channel list for a specific channel tab thanks to the AJAX request.
 *
 * @param {*} page The page.
 * @param {*} id The channel tab identifier.
 *
 * @returns The AJAX request promise.
 */
function getChannelsForSpecificChannelTabs(page, id = 0) {
  let url = "";
  if (id == 0)
    url = `${GET_CHANNELS_FOR_SPECIFIC_CHANNEL_TAB_REQUEST_URL}?page=${page}`;
  else
    url = `${GET_CHANNELS_FOR_SPECIFIC_CHANNEL_TAB_REQUEST_URL}?page=${page}&id=${id}`;
  return new Promise(function (resolve, reject) {
    let xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        if (xhr.status === 200) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          reject(new Error("Request failed with status " + xhr.status));
        }
      }
    };
    xhr.send();
  });
}

/**
 * Get the channel tab list thanks to the AJAX request.
 *
 * @param {boolean} nameOnly If this options is `true`, the channel tab list contains the name of tab only.
 *
 * @returns The AJAX request promise.
 */
function getChannelTabsAjaxRequest() {
  let url = GET_CHANNEL_TAGS_REQUEST_URL;
  return new Promise(function (resolve, reject) {
    let xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        if (xhr.status === 200) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          reject(new Error("Request failed with status " + xhr.status));
        }
      }
    };
    xhr.send();
  });
}

/**
 * Get the theme list for a specific channel thanks to the AJAX request.
 *
 * @param {string} channelSlug The channel slug.
 *
 * @returns The AJAX request promise.
 */
function getThemesForSpecificChannel(channelSlug) {
  let url = GET_THEMES_FOR_SPECIFIC_CHANNEL_REQUEST_URL.replace(
    "/__SLUG__/",
    channelSlug,
  );
  return new Promise(function (resolve, reject) {
    let xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        if (xhr.status === 200) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          reject(new Error("Request failed with status " + xhr.status));
        }
      }
    };
    xhr.send();
  });
}

/**
 * Set the modal title when the user ask to view this modal.
 *
 * @param {HTMLElement} modalContentElement The HTML element of the modal.
 * @param {Array} channelsArray The channel list.
 */
function setModalTitle(modalContentElement, channelsCount) {
  const modalTitleElement = modalContentElement.querySelector(".modal-title");
  const channelIcon = '<i class="bi bi-play-btn" aria-hidden="true"></i>';
  var channelString = ngettext(
    `%(count)s channel`,
    `%(count)s channels`,
    channelsCount,
  );
  channelString = interpolate(channelString, { count: channelsCount }, true);
  modalTitleElement.innerHTML = `${channelIcon}&nbsp;${channelString}`;
}

/**
 * Convert a channel list to HTML modal list.
 *
 * @param {Array} channelsArray The channel list.
 *
 * @returns The HTML modal list.
 */
function convertToModalList(channelsArray) {
  const channelListGroupElement = document.createElement("ul");
  if (channelsArray.length > 0) {
    channelListGroupElement.classList.add(
      "clist-group",
      "list-group-flush",
      "p-0",
    );
    channelListGroupElement.id = "list-channels";
    channelsArray.forEach((channel) => {
      channelListGroupElement.appendChild(convertToModalListElement(channel));
    });
  } else {
    const channelListElement = document.createElement("li");
    channelListElement.classList.add(
      "list-group-item",
      "list-group-item-action",
    );
    channelListElement.textContent = gettext("No channels found");
    channelListGroupElement.appendChild(channelListElement);
  }
  return channelListGroupElement;
}

/**
 * Convert a channel to a HTML modal list element.
 *
 * @param {any} channel The channel to convert.
 *
 * @returns The HTML modal list element.
 */
function convertToModalListElement(channel) {
  const haveThemes = channel.themes > 0;
  const channelListElement = document.createElement("li");
  channelListElement.classList.add("list-group-item", "list-group-item-action");
  channelListElement.setAttribute("data-id", channel.id);
  const dFlexDivElement = document.createElement("div");
  dFlexDivElement.classList.add(
    "d-flex",
    "justify-content-between",
    "align-items-center",
  );
  const dFlexSpanElement = document.createElement("span");
  dFlexSpanElement.classList.add(
    "d-flex",
    "align-items-center",
    "title-chaine",
  );
  dFlexSpanElement.innerHTML =
    '<i class="bi bi-play-btn pod-channel__item"></i>';
  const linkElement = document.createElement("a");
  linkElement.setAttribute("href", channel.url);
  linkElement.id = `channel-title_${channel.id}`;
  linkElement.textContent = channel.title;
  const noWrapSpanElement = document.createElement("span");
  noWrapSpanElement.classList.add("text-nowrap");
  if (haveThemes) {
    spanElement = setChannelThemeButtonForModal(noWrapSpanElement, channel);
  }

  var videoString = ngettext(
    `%(count)s video`,
    `%(count)s videos`,
    channel.videoCount,
  );
  videoString = interpolate(videoString, { count: channel.videoCount }, true);
  noWrapSpanElement.innerHTML += `<span class="badge text-bg-primary rounded-pill">${videoString}</span>`;

  const childAndParentCouples = [
    [dFlexSpanElement, linkElement],
    [dFlexDivElement, dFlexSpanElement],
    [dFlexDivElement, noWrapSpanElement],
    [channelListElement, dFlexDivElement],
  ];
  childAndParentCouples.forEach((childAndParentCouple) => {
    childAndParentCouple[0].appendChild(childAndParentCouple[1]);
  });
  setImageForModal(dFlexSpanElement, channel);
  if (haveThemes) {
    setChannelThemeCollapseForModal(channelListElement, spanElement, channel);
  }
  return channelListElement;
}

/**
 * Set the image in the innerHTML of span HTML element.
 *
 * @param {HTMLElement} dFlexSpanElement The span HTML element.
 * @param {any} channel The channel element.
 */
function setImageForModal(dFlexSpanElement, channel) {
  if (channel.headband) {
    dFlexSpanElement.innerHTML += `<img src="${channel.headbandImage}" height="34" class="rounded" alt="" loading="lazy">`;
  }
}

/**
 * Set a channel theme collapse for the modal.
 *
 * @param {HTMLElement} channelListElement The HTML element channel list.
 * @param {any} channel The channel element.
 */
function setChannelThemeCollapseForModal(
  channelListElement,
  spanElement,
  channel,
) {
  const themesCollapseElement = document.createElement("div");
  const themesListElement = document.createElement("ul");
  let themesLoaded = false;
  let open = false;
  themesCollapseElement.id = `collapseTheme${channel.id}`;
  themesCollapseElement.classList.add("collapsibleThemes", "collapse");
  setAttributesWithTab(themesCollapseElement, [
    ["aria-labelledby", `channel-title_${channel.id}`],
    ["data-bs-parent", `#list-channels`],
    ["data-id", `${channel.id}`],
    ["aria-controls", `collapseTheme${channel.id}`],
  ]);
  themesListElement.classList.add("list-group");
  themesCollapseElement.appendChild(themesListElement);
  channelListElement.appendChild(themesCollapseElement);
  spanElement.addEventListener("click", function () {
    open = !open;
    if (open) {
      spanElement.querySelector(".bi").classList.remove("bi-chevron-down");
      spanElement.querySelector(".bi").classList.add("bi-chevron-up");
    } else {
      spanElement.querySelector(".bi").classList.remove("bi-chevron-up");
      spanElement.querySelector(".bi").classList.add("bi-chevron-down");
    }
    if (themesLoaded === false) {
      spanElement.querySelector(".btn").style.backgroundColor = "gray";
      getThemesForSpecificChannel(channel.url)
        .then(function (themes) {
          themes.forEach((channelTheme) => {
            addThemeInList(themesListElement, channelTheme);
          });
          spanElement.querySelector(".btn").style.backgroundColor = "inherit";
        })
        .catch(function (error) {
          console.error(error);
        });
      themesLoaded = true;
    }
  });
}

/**
 * Add a theme in a list.
 *
 * @param {HTMLElement} listElement The HTML element list.
 * @param {any} theme The theme.
 */
function addThemeInList(listElement, theme) {
  const themeLiElement = document.createElement("li");
  const linkThemeElement = document.createElement("a");
  themeLiElement.classList.add("list-group-item");
  themeLiElement.style.marginRight = "1em";
  linkThemeElement.textContent = theme.title;
  linkThemeElement.setAttribute("href", theme.url);
  themeLiElement.appendChild(linkThemeElement);
  if (theme.child.length > 0) {
    const themesListElement = document.createElement("ul");
    themesListElement.classList.add("list-group", "list-group-flush");
    themeLiElement.appendChild(themesListElement);
    theme.child.forEach((channelTheme) => {
      addThemeInList(themesListElement, channelTheme);
    });
  }
  listElement.appendChild(themeLiElement);
}

/**
 * Append child to span HTML element. This child is the theme button element.
 *
 * @param {HTMLElement} spanElement The span HTML element.
 * @param {any} channel The channel.
 */
function setChannelThemeButtonForModal(spanElement, channel) {
  const themesButtonElement = document.createElement("button");
  themesButtonElement.classList.add("btn", "btn-link", "collapsed");
  setAttributesWithTab(themesButtonElement, [
    ["data-bs-toggle", "collapse"],
    ["data-bs-target", `#collapseTheme${channel.id}`],
    ["aria-expanded", "false"],
    ["aria-controls", `collapseTheme${channel.id}`],
  ]);
  if (channel.themes > 1) {
    themesButtonElement.innerHTML = `${channel.themes} thèmes <i class="bi bi-chevron-down"></i>`;
  } else {
    themesButtonElement.innerHTML = `${channel.themes} thème <i class="bi bi-chevron-down"></i>`;
  }
  spanElement.appendChild(themesButtonElement);
  return spanElement;
}

/**
 * Create modal for a specific channel tab.
 *
 * @param {any} channelTab The specific channel tab.
 */
function createModalFor(channelTab) {
  const headerElement = document.getElementsByTagName("header")[0];
  const modalElement = document.createElement("div");
  modalElement.classList.add("modal", "fade", `chaines-modal-${channelTab.id}`);
  setAttributesWithTab(modalElement, [
    ["tabindex", "-1"],
    ["role", "dialog"],
    ["aria-hidden", "true"],
  ]);
  modalElement.innerHTML = `
        <div class="modal-dialog modal-lg modal-pod-full">
            <div class="modal-content">
                <div class="modal-header">
                    <h2 class="modal-title">
                        <i class="bi bi-play-btn"></i>&nbsp;
                        <span class="spinner-border text-primary" role="status">
                        </span>
                    </h2>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="${gettext(
                      "Close",
                    )}"></button>
                </div>
            <div class="modal-body">
                <div class="text-center">
                    <span class="spinner-border text-primary" role="status">
                    </span>
            </div>
            </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">${gettext(
                      "Close",
                    )}</button>
                </div>
            </div>
        </div>
    `;
  headerElement.appendChild(modalElement);
  let allChannelsLoaded = false;
  modalElement.addEventListener("shown.bs.modal", function () {
    const modalContentElement = this.querySelector(".modal-content");
    let currentPage = 1;
    if (allChannelsLoaded === false) {
      getChannelsForSpecificChannelTabs(currentPage, channelTab.id)
        .then(function (channels) {
          let channelsArray = Object.values(channels["channels"]);
          setModalTitle(modalContentElement, channels["count"]);
          modalContentElement
            .querySelector(".modal-body")
            .appendChild(convertToModalList(channelsArray));
          modalContentElement
            .querySelector(".modal-body")
            .querySelector(".text-center")
            .remove();
          currentPage++;
          loadNextBatchOfChannels(
            modalContentElement,
            currentPage,
            allChannelsLoaded,
            getChannelsForSpecificChannelTabs,
            channelTab.id,
          );
        })
        .catch(function (error) {
          console.error(error);
        });
      allChannelsLoaded = true;
    }
  });
}

/**
 * Load the next batch of channels.
 *
 * @param {HTMLElement} modalContentElement The modal content HTML element.
 * @param {number} currentPage The current page.
 * @param {boolean} allChannelsLoaded `true` if all channels loaded, `false` otherwise.
 */
function loadNextBatchOfChannels(
  modalContentElement,
  currentPage,
  allChannelsLoaded,
  fetchDataFunction,
  channelTabId,
) {
  const loaderElement = document.createElement("div");
  loaderElement.classList.add("text-center");
  loaderElement.innerHTML =
    '<span class="spinner-border text-primary" role="status"></span>';
  modalContentElement.querySelector(".modal-body").appendChild(loaderElement);
  fetchDataFunction(currentPage, channelTabId)
    .then(function (channels) {
      let channelsArray = Object.values(channels["channels"]);
      if (currentPage <= channels["totalPages"]) {
        channelsArray.forEach((channel) => {
          modalContentElement
            .querySelector(".clist-group")
            .appendChild(convertToModalListElement(channel));
          loaderElement.remove();
        });
        currentPage++;
        loadNextBatchOfChannels(
          modalContentElement,
          currentPage,
          allChannelsLoaded,
          fetchDataFunction,
          channelTabId,
        );
      } else {
        allChannelsLoaded = true;
        const loaderBisElement = modalContentElement
          .querySelector(".modal-body")
          .querySelector(".text-center");
        if (loaderBisElement) {
          loaderBisElement.remove();
        }
      }
    })
    .catch(function (error) {
      console.error(error);
    });
}

const channelModal = document.querySelector(".chaines-modal");
let allChannelsLoaded = false;
channelModal.addEventListener("shown.bs.modal", function () {
  const modalContentElement = this.querySelector(".modal-content");
  let currentPage = 1;
  if (allChannelsLoaded === false) {
    //getChannelsAjaxRequest()
    getChannelsForSpecificChannelTabs(currentPage)
      .then(function (channels) {
        let channelsArray = Object.values(channels["channels"]);
        setModalTitle(modalContentElement, channels["count"]);
        modalContentElement
          .querySelector(".modal-body")
          .appendChild(convertToModalList(channelsArray));
        modalContentElement
          .querySelector(".modal-body")
          .querySelector(".text-center")
          .remove();
        currentPage++;
        loadNextBatchOfChannels(
          modalContentElement,
          currentPage,
          allChannelsLoaded,
          getChannelsForSpecificChannelTabs,
        );
      })
      .catch(function (error) {
        console.error(error);
      });
    allChannelsLoaded = true;
  }
});

const burgerMenu = document.getElementById("pod-navbar__menu");
let burgerMenuLoaded = false;
burgerMenu.addEventListener("shown.bs.offcanvas", function () {
  if (burgerMenuLoaded === false) {
    const navChannelTabs = document.getElementById("tab-list");
    getChannelTabsAjaxRequest()
      .then(function (channelTabs) {
        let channelTabsArray = Object.values(channelTabs);
        burgerMenu.querySelector(".progress").remove();
        channelTabsArray.forEach((channelTab) => {
          const navChannelTab = document.createElement("li");
          const buttonChannelTab = document.createElement("button");
          navChannelTab.classList.add("nav-item");
          buttonChannelTab.classList.add("nav-link");
          setAttributesWithTab(buttonChannelTab, [
            ["data-bs-toggle", "modal"],
            ["data-bs-target", `.chaines-modal-${channelTab.id}`],
          ]);
          buttonChannelTab.innerHTML = `<i class="bi bi-play-btn pod-nav-link-icon"></i> ${channelTab.name}`;
          createModalFor(channelTab);
          navChannelTab.appendChild(buttonChannelTab);
          navChannelTabs.appendChild(navChannelTab);
        });
      })
      .catch(function (error) {
        console.error(error);
      });
    burgerMenuLoaded = true;
  }
});
