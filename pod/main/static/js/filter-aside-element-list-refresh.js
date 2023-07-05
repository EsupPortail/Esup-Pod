var sortDirectionChars = ["8600", "8599"];
var sortDirectionTitle = [
    gettext("Descending sort"),
    gettext("Ascending sort"),
];

/**
 * Update arrow char of ascending or descending sort order.
 * @param {*} sortDirectionAsc
 */
function updateSortDirectionChar(sortDirectionAsc) {
    document.getElementById("sort_direction_label").innerHTML =
    "&#" + sortDirectionChars[+sortDirectionAsc].toString();
}

/**
 * Update title for input sort direction.
 * @param {*} sortDirectionAsc 
 */
function updateSortDirectionTitle(sortDirectionAsc) {
    let newTitle = sortDirectionTitle[+sortDirectionAsc];
    document
        .getElementById("sort_direction_label")
        .setAttribute("title", newTitle);
}

/**
 * Toggle direction of sort.
 */
function toggleSortDirection() {
    document.getElementById("sort_direction").checked =
    !document.getElementById("sort_direction").checked;
    const direction = document.getElementById("sort_direction").checked;
    updateSortDirectionChar(direction);
    updateSortDirectionTitle(direction);
}
