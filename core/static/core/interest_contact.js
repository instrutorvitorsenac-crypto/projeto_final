(() => {
  const dialog = document.querySelector("[data-contact-dialog]");
  if (!dialog) {
    return;
  }

  const close = dialog.querySelector("[data-close-contact]");
  document.querySelector("[data-open-contact]")?.addEventListener("click", () => {
    dialog.showModal();
  });
  close?.addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) {
      dialog.close();
    }
  });

  if (dialog.hasAttribute("data-open-on-load")) {
    dialog.showModal();
  }
})();
