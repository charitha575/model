function search() {
    const fileInput = document.getElementById("fileInput");
    const file = fileInput.files[0];

    if (!file) {
        alert("Upload image first");
        return;
    }

    // Show preview
    const preview = document.getElementById("preview");
    preview.innerHTML = `<img src="${URL.createObjectURL(file)}">`;

    const formData = new FormData();
    formData.append("image", file);

    const resultsDiv = document.getElementById("results");
    const title = document.getElementById("resultTitle");

    resultsDiv.innerHTML = "🔄 Searching...";
    title.innerText = "";

    fetch("/search", {
        method: "POST",
        body: formData
    })
    .then(res => res.json())
    .then(data => {

        resultsDiv.innerHTML = "";

        if (data.error) {
            resultsDiv.innerHTML = data.error;
            return;
        }

        title.innerText = `Top ${data.results.length} Matches`;

        data.results.forEach(r => {

            // Extract label from path
            let parts = r.image.split("/");
            let label = parts[parts.length - 2];

            // Convert score
            let score = (1 - r.score).toFixed(2);

            const card = document.createElement("div");
            card.className = "card";

            card.innerHTML = `
                <img src="${r.image}">
                <p class="score">Confidence: ${score}</p>
                <p class="label">${label}</p>
            `;

            resultsDiv.appendChild(card);
        });
    });
}