(() => {
  const input = document.getElementById("id_images");
  const preview = document.querySelector("[data-image-preview]");

  if (!input || !preview) {
    return;
  }

  let previewUrls = [];

  input.addEventListener("change", () => {
    previewUrls.forEach((url) => URL.revokeObjectURL(url));
    previewUrls = [];
    preview.replaceChildren();

    Array.from(input.files).forEach((file) => {
      const item = document.createElement("figure");
      item.className = "image-preview-item";
      const extension = file.name.split(".").pop().toLowerCase();

      const image = document.createElement("img");
      const url = URL.createObjectURL(file);
      previewUrls.push(url);
      image.src = url;
      image.alt = `Prévia de ${file.name}`;
      image.addEventListener("error", () => {
        image.remove();
        const format = document.createElement("span");
        format.className = "image-preview-format";
        format.textContent = `${extension.toUpperCase()} · prévia não suportada neste navegador`;
        item.prepend(format);
      }, { once: true });
      item.append(image);

      const caption = document.createElement("figcaption");
      caption.textContent = `${file.name} · ${(file.size / 1024 / 1024).toFixed(1)} MB`;
      item.append(caption);
      preview.append(item);
    });
  });

  window.addEventListener("beforeunload", () => {
    previewUrls.forEach((url) => URL.revokeObjectURL(url));
  });
})();
