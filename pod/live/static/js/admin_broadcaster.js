/**
 * @file Esup-Pod broadcaster administration form behavior.
 */
document.addEventListener("DOMContentLoaded", function () {
  const streamMode = document.getElementById("id_stream_mode");
  if (streamMode) {
    /** Mark the fields required by the selected broadcaster playback mode. */
    const updateStreamFields = () => {
      const live = streamMode.value === "esup_runner";
      ["url", "runner_manager", "source_id"].forEach((name) => {
        const field = document.getElementById("id_" + name);
        if (!field) return;
        const required = name === "url" ? !live : live;
        field.required = required;
        const row = field.closest(".form-row");
        if (row) {
          row.querySelectorAll("label").forEach((label) => {
            label.classList.toggle("required", required);
          });
        }
      });
    };
    updateStreamFields();
    streamMode.addEventListener("change", updateStreamFields);
  }
  const implementation_select = document.getElementById(
    "id_piloting_implementation",
  );
  const implementation_config = document.getElementById("id_piloting_conf");

  if (implementation_select && implementation_config) {
    changeImplPlaceholder();
    implementation_select.addEventListener("change", changeImplPlaceholder);
  }

  /**
   * Change the placeholder in the broadcaster admin view.
   *
   * When selecting a 'piloting_implementation' it fetches and display the mandatory parameters as a placeholder in the piloting_conf field.
   */
  function changeImplPlaceholder() {
    const selected_impl = implementation_select.value;

    if (selected_impl === "") return;

    // find mandatory param
    let url = implementation_config.dataset.url + selected_impl;
    fetch(url, {
      method: "GET",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then((response) => {
        if (response.ok) return response.json();
        else return Promise.reject(response);
      })
      .then((r) => {
        implementation_config.setAttribute(
          "placeholder",
          JSON.stringify(r, null, 4),
        );
      })
      .catch(() => {
        alert(gettext("An error occurred"));
      });
  }
});
