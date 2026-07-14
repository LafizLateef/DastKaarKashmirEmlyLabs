// ===============================
// DASTKAAR PRODUCTS — ADD / EDIT / DELETE
// ===============================

const MAX_IMAGE_BYTES = 8 * 1024 * 1024;
const ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png"];

document.addEventListener("DOMContentLoaded", () => {

    const addBtn = document.getElementById("btn-save-product");
    if (addBtn) addBtn.addEventListener("click", handleAddProduct);

    const editBtn = document.getElementById("btn-save-edit-product");
    if (editBtn) editBtn.addEventListener("click", handleEditProduct);

    const deleteBtn = document.getElementById("btn-confirm-delete-product");
    if (deleteBtn) deleteBtn.addEventListener("click", handleDeleteProduct);

    document.querySelectorAll('[data-modal-open="modal-add-product"]').forEach((btn) => {
        btn.addEventListener("click", resetAddForm);
    });

    document.querySelectorAll('[data-modal-open="modal-edit-product"]').forEach((btn) => {
        btn.addEventListener("click", () => populateEditForm(btn));
    });

    document.querySelectorAll('[data-modal-open="modal-delete-product"]').forEach((btn) => {
        btn.addEventListener("click", () => {
            document.getElementById("modal-delete-product").dataset.productId = btn.dataset.productId;
        });
    });

    wireImagePicker("add");
    wireImagePicker("edit");

});

function wireImagePicker(prefix) {

    const input = document.getElementById(`${prefix}-images`);
    if (!input) return;

    input.addEventListener("change", () => {

        const file = input.files[0];
        if (!file) return;

        if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
            alert("Please choose a JPG or PNG image.");
            input.value = "";
            return;
        }

        if (file.size > MAX_IMAGE_BYTES) {
            alert("Image is too large (8MB max).");
            input.value = "";
            return;
        }

        const reader = new FileReader();
        reader.onload = () => showImagePreview(prefix, reader.result);
        reader.readAsDataURL(file);

    });

}

function showImagePreview(prefix, src) {

    const preview = document.getElementById(`${prefix}-image-preview`);
    const icon = document.getElementById(`${prefix}-dropzone-icon`);
    const text = document.getElementById(`${prefix}-dropzone-text`);

    preview.src = src;
    preview.style.display = "block";
    if (icon) icon.style.display = "none";
    if (text) text.innerHTML = "<strong>Change image</strong>";

}

function hideImagePreview(prefix) {

    const preview = document.getElementById(`${prefix}-image-preview`);
    const icon = document.getElementById(`${prefix}-dropzone-icon`);
    const text = document.getElementById(`${prefix}-dropzone-text`);

    preview.removeAttribute("src");
    preview.style.display = "none";
    if (icon) icon.style.display = "";
    if (text) text.innerHTML = "<strong>Click to upload</strong> or drag and drop";

}

function resetAddForm() {

    document.getElementById("add-name").value = "";
    document.getElementById("add-category").selectedIndex = 0;
    document.getElementById("add-price").value = "";
    document.getElementById("add-stock").value = "";
    document.getElementById("add-description").value = "";
    document.getElementById("add-images").value = "";
    hideImagePreview("add");

}

function populateEditForm(btn) {

    document.getElementById("modal-edit-product").dataset.productId = btn.dataset.productId;
    document.getElementById("edit-name").value = btn.dataset.name || "";
    document.getElementById("edit-category").value = btn.dataset.category || "";
    document.getElementById("edit-price").value = btn.dataset.price || "";
    document.getElementById("edit-stock").value = btn.dataset.stock || "";
    document.getElementById("edit-description").value = btn.dataset.description || "";
    document.getElementById("edit-images").value = "";

    if (btn.dataset.imageUrl) {
        showImagePreview("edit", btn.dataset.imageUrl);
    } else {
        hideImagePreview("edit");
    }

}

function readProductForm(prefix) {

    return {
        name: document.getElementById(`${prefix}-name`).value.trim(),
        category: document.getElementById(`${prefix}-category`).value,
        price: document.getElementById(`${prefix}-price`).value,
        stock: document.getElementById(`${prefix}-stock`).value,
        description: document.getElementById(`${prefix}-description`).value.trim(),
        image: document.getElementById(`${prefix}-images`).files[0] || null
    };

}

function validateProductForm(payload) {

    if (!payload.name) return "Please enter a product name.";
    if (payload.price === "" || Number.isNaN(Number(payload.price))) return "Please enter a valid price.";
    if (payload.stock === "" || Number.isNaN(Number(payload.stock))) return "Please enter a valid stock quantity.";
    return null;

}

function buildProductFormData(payload) {

    const formData = new FormData();
    formData.append("name", payload.name);
    formData.append("category", payload.category);
    formData.append("price", payload.price);
    formData.append("stock", payload.stock);
    formData.append("description", payload.description);
    if (payload.image) formData.append("images", payload.image);

    return formData;

}

async function handleAddProduct() {

    const payload = readProductForm("add");
    const error = validateProductForm(payload);

    if (error) {
        alert(error);
        return;
    }

    const btn = document.getElementById("btn-save-product");
    btn.disabled = true;

    try {

        const res = await fetch("/api/products", {
            method: "POST",
            body: buildProductFormData(payload)
        });

        const data = await res.json();

        if (data.success) {
            window.location.reload();
        } else {
            alert(data.message || "Could not save product.");
        }

    } catch (err) {
        console.error(err);
        alert("Could not save product. Please try again.");
    } finally {
        btn.disabled = false;
    }

}

async function handleEditProduct() {

    const modal = document.getElementById("modal-edit-product");
    const id = modal.dataset.productId;
    if (!id) return;

    const payload = readProductForm("edit");
    const error = validateProductForm(payload);

    if (error) {
        alert(error);
        return;
    }

    const btn = document.getElementById("btn-save-edit-product");
    btn.disabled = true;

    try {

        const res = await fetch(`/api/products/${encodeURIComponent(id)}`, {
            method: "PUT",
            body: buildProductFormData(payload)
        });

        const data = await res.json();

        if (data.success) {
            window.location.reload();
        } else {
            alert(data.message || "Could not update product.");
        }

    } catch (err) {
        console.error(err);
        alert("Could not update product. Please try again.");
    } finally {
        btn.disabled = false;
    }

}

async function handleDeleteProduct() {

    const modal = document.getElementById("modal-delete-product");
    const id = modal.dataset.productId;
    if (!id) return;

    const btn = document.getElementById("btn-confirm-delete-product");
    btn.disabled = true;

    try {

        const res = await fetch(`/api/products/${encodeURIComponent(id)}`, {
            method: "DELETE"
        });

        const data = await res.json();

        if (data.success) {
            window.location.reload();
        } else {
            alert(data.message || "Could not delete product.");
        }

    } catch (err) {
        console.error(err);
        alert("Could not delete product. Please try again.");
    } finally {
        btn.disabled = false;
    }

}
