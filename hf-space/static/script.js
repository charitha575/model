// Load stats on page load
window.onload = function() {
    loadStats();
};

function getApiKey() {
    return document.getElementById("apiKey").value || "";
}

function loadStats() {
    fetch("/stats")
        .then(res => res.json())
        .then(data => {
            document.getElementById("statsBar").innerText =
                "Total Products Indexed: " + data.total_images;
        })
        .catch(() => {
            document.getElementById("statsBar").innerText = "Could not load stats";
        });
}

// Tab switching
function showTab(tab) {
    document.getElementById("addTab").style.display = tab === "add" ? "block" : "none";
    document.getElementById("searchTab").style.display = tab === "search" ? "block" : "none";
    document.getElementById("tabAdd").className = tab === "add" ? "tab active" : "tab";
    document.getElementById("tabSearch").className = tab === "search" ? "tab active" : "tab";
}

// ADD PRODUCT
function addProduct() {
    const fileInput = document.getElementById("addFileInput");
    const file = fileInput.files[0];
    const productId = document.getElementById("productId").value || "product_" + Date.now();
    const category = document.getElementById("category").value || "uncategorized";

    if (!file) {
        alert("Select an image first");
        return;
    }

    // Show preview
    document.getElementById("addPreview").innerHTML =
        '<img src="' + URL.createObjectURL(file) + '">';

    document.getElementById("addResult").innerHTML =
        '<div class="success-msg">Adding to index...</div>';

    const formData = new FormData();
    formData.append("image", file);
    formData.append("product_id", productId);
    formData.append("category", category);

    fetch("/add-image", {
        method: "POST",
        headers: { "X-API-Key": getApiKey() },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            document.getElementById("addResult").innerHTML =
                '<div class="success-msg">Added! Product ID: ' + data.product_id +
                ' | Total indexed: ' + data.total_images + '</div>';
            loadStats();
            // Clear form
            document.getElementById("productId").value = "";
            document.getElementById("category").value = "";
        } else {
            document.getElementById("addResult").innerHTML =
                '<div class="error-msg">Error: ' + data.error + '</div>';
        }
    })
    .catch(err => {
        document.getElementById("addResult").innerHTML =
            '<div class="error-msg">Network error: ' + err + '</div>';
    });
}

// SEARCH
function searchProduct() {
    const fileInput = document.getElementById("searchFileInput");
    const file = fileInput.files[0];

    if (!file) {
        alert("Upload image first");
        return;
    }

    document.getElementById("searchPreview").innerHTML =
        '<img src="' + URL.createObjectURL(file) + '">';

    const formData = new FormData();
    formData.append("image", file);

    const resultsDiv = document.getElementById("results");
    const title = document.getElementById("resultTitle");

    resultsDiv.innerHTML = "Searching...";
    title.innerText = "";

    fetch("/search", {
        method: "POST",
        headers: { "X-API-Key": getApiKey() },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        resultsDiv.innerHTML = "";

        if (data.error) {
            resultsDiv.innerHTML = '<div class="error-msg">' + data.error + '</div>';
            return;
        }

        if (data.results.length === 0) {
            resultsDiv.innerHTML = '<div class="error-msg">No matches found. Add some products first!</div>';
            return;
        }

        title.innerText = "Top " + data.results.length + " Matches";

        data.results.forEach(function(r) {
            var parts = r.image.split("/");
            var label = parts[parts.length - 2] || "product";

            var score = (1 / (1 + r.score) * 100).toFixed(1) + "%";

            var card = document.createElement("div");
            card.className = "card";

            card.innerHTML =
                '<img src="' + r.image + '">' +
                '<p class="score">Confidence: ' + score + '</p>' +
                '<p class="label">' + label + '</p>';

            resultsDiv.appendChild(card);
        });
    })
    .catch(function(err) {
        resultsDiv.innerHTML = '<div class="error-msg">Search failed: ' + err + '</div>';
    });
}

// RESET INDEX
function resetIndex() {
    if (!confirm("This will DELETE all indexed products. Are you sure?")) {
        return;
    }

    fetch("/reset", {
        method: "POST",
        headers: { "X-API-Key": getApiKey() }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert("Index cleared! Total images: 0");
            loadStats();
        } else {
            alert("Error: " + data.error);
        }
    })
    .catch(err => alert("Reset failed: " + err));
}
