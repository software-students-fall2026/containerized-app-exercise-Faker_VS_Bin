const fileInput = document.querySelector("#receipt-file");
const preview = document.querySelector("#preview");
const message = document.querySelector("#message");
const removeButton = document.querySelector("#remove-receipt");

const ALLOWED_TYPES = new Set(["image/png", "image/jpeg"]);
const MAX_BYTES = 5_000_000;

let previewUrl = null;
let selectionVersion = 0;

function clearPreview() {
  preview.hidden = true;
  preview.removeAttribute("src");

  if (previewUrl !== null) {
    URL.revokeObjectURL(previewUrl);
    previewUrl = null;
  }
}

function resetSelection(text = "") {
  selectionVersion += 1;
  clearPreview();

  fileInput.value = "";
  fileInput.removeAttribute("aria-invalid");
  removeButton.disabled = true;
  message.textContent = text;
}

function rejectFile(text) {
  resetSelection(text);
  fileInput.setAttribute("aria-invalid", "true");
}

fileInput.addEventListener("change", async () => {
  const file = fileInput.files[0];

  if (!file) {
    resetSelection();
    return;
  }

  const thisSelection = ++selectionVersion;

  clearPreview();
  fileInput.removeAttribute("aria-invalid");
  removeButton.disabled = false;

  if (!ALLOWED_TYPES.has(file.type)) {
    rejectFile("Choose a PNG or JPEG image.");
    return;
  }

  if (file.size === 0) {
    rejectFile("This file is empty. Choose another image.");
    return;
  }

  if (file.size > MAX_BYTES) {
    rejectFile("This image is too large. The limit is 5 MB.");
    return;
  }

  message.textContent = "Checking image…";

  const url = URL.createObjectURL(file);
  previewUrl = url;

  const image = new Image();
  image.src = url;

  try {
    await image.decode();

    // A newer selection or removal makes this result obsolete.
    if (thisSelection !== selectionVersion) {
      return;
    }

    preview.src = url;
    preview.hidden = false;
    message.textContent = `Preview ready: ${file.name}`;
  } catch {
    if (thisSelection !== selectionVersion) {
      return;
    }

    rejectFile("This image could not be opened. Choose another image.");
  }
});

removeButton.addEventListener("click", () => {
  resetSelection("Receipt removed.");
  fileInput.focus();
});