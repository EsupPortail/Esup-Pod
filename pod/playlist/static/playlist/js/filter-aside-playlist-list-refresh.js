/**
 * Return url with filter and sort parameters.
 *
 * @returns The new URL.
 */
function getUrlForRefresh() {
    let newUrl = window.location.pathname;
    let urlParams = new URLSearchParams(window.location.search);
    let visibilityParam = urlParams.get('visibility');
    // Add sort-related parameters
    newUrl += "?visibility=" + visibilityParam + "&sort=" + document.getElementById("sort").value + "&";
    var sortDirectionAsc = document.getElementById("sort_direction").checked;
    if (sortDirectionAsc) {
        newUrl +=
            "sort_direction=" + document.getElementById("sort_direction").value + "&";
    }
    window.history.pushState({}, '', newUrl);
    return newUrl;
}

/**
 * Updates playlist list.
 */
function refreshPlaylistsSearch() {
    url = getUrlForRefresh();
    fetch(url, {
        method: "GET",
        headers: {
            "X-CSRFToken": "{{ csrf_token }}",
            "X-Requested-With": "XMLHttpRequest",
        },
        dataType: "html",
        cache: "no-cache",
    })
        .then((response) => response.text())
        .then((data) => {
            let parser = new DOMParser();
            let html = parser.parseFromString(data, "text/html");
            document.getElementById("playlists_list").replaceWith(html.getElementById("playlists_list"));
        })
        .catch((error) => {
            document.getElementById("playlists_list").innerHTML = gettext(
                "An Error occurred while processing."
            );
        });
}

// Add trigger event to manage sort direction.
document
    .getElementById('sort_direction_label')
    .addEventListener('click', function (e) {
        e.preventDefault();
        toggleSortDirection();
        refreshPlaylistsSearch();
    });
document.getElementById('sort').addEventListener('change', function (e) {
    refreshPlaylistsSearch();
});
