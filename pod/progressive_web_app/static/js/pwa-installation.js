let installPrompt = null;
let installButton = null;
let isInstalled = window.matchMedia("(display-mode:standalone)").matches;

document.addEventListener("DOMContentLoaded", function () {
  installButton = document.querySelector("#pwa-install-container");

  if (!installButton) {
    return;
  }

  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    installPrompt = event;
    if (!isInstalled) {
      installButton.classList.remove("d-none");
    }
  });

  installButton.addEventListener("click", async () => {
    if (!installPrompt) {
      return;
    }
    const result = await installPrompt.prompt();
    if (result.outcome == "accepted") {
      installButton.classList.add("d-none");
    }
  });
});
