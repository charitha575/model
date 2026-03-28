from flask import Flask, render_template, request, jsonify, send_file
import os
from retrieval_system import ImageRetrievalSystem

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ LOAD EXISTING INDEX (NO RE-INDEXING)
retrieval_system = ImageRetrievalSystem(
    index_path="image_index.faiss",
    metadata_path="image_metadata.json"
)

# ✅ HOME PAGE
@app.route("/")
def index():
    return render_template("index.html")


# ✅ SEARCH API
@app.route("/search", methods=["POST"])
def search():
    if "image" not in request.files:
        return jsonify({"error": "No file uploaded"})

    file = request.files["image"]
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    try:
        results = retrieval_system.search(filepath)
        output = []
        selected_scores = []
        extra_results = []

        THRESHOLD = 0.08   # 🔥 tweak if needed

        # Step 1: pick diverse results
        for path, score in results:
            fixed_path = path.replace("\\", "/")

            # 🚫 skip visually similar
            if any(abs(score - s) < THRESHOLD for s in selected_scores):
                extra_results.append((fixed_path, score))
                continue

            selected_scores.append(score)

            output.append({
                "image": f"/image?path={fixed_path}",
                "score": float(score)
            })

            if len(output) == 5:
                break

        # Step 2: fill remaining slots (if less than 5)
        for path, score in extra_results:
            if len(output) == 5:
                break

            output.append({
                "image": f"/image?path={path}",
                "score": float(score)
            })

        return jsonify({"results": output})

    except Exception as e:
        return jsonify({"error": str(e)})


# ✅ IMAGE SERVING ROUTE (CRITICAL FIX)
@app.route("/image")
def serve_image():
    path = request.args.get("path")

    if not os.path.exists(path):
        return "Image not found", 404

    return send_file(path)


if __name__ == "__main__":
    app.run(debug=True)