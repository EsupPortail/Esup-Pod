document.addEventListener("DOMContentLoaded", function() {

  const implementation_select = document.getElementById("id_piloting_implementation");
  const implementation_config = document.getElementById("id_piloting_conf");

  if (implementation_select && implementation_config) {
    changeImplPlaceholder();
    implementation_select.addEventListener("change", changeImplPlaceholder);
  }

  function changeImplPlaceholder() {
    const selected_impl = implementation_select.value

    if (selected_impl === "")
      return

    // find mandatory param
    let url =
      "/live/ajax_calls/getmandatoryparameters/?impl_name=" + selected_impl;

    fetch(url, {
      method: "GET",
      headers: {
        "X-Requested-With": "XMLHttpRequest"
      }
    })
      .then((response) => {
        if (response.ok)
          return response.json();
        else
          return Promise.reject(response);
      })
      .then((r) => {
        implementation_config.setAttribute("placeholder", JSON.stringify(r, null, 4));
      })
      .catch(() => {
        alert(gettext("An error occurred"));
      });

  }

});