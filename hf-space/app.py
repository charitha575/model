from flask import Flask, render_template, request, jsonify, send_file
from functools import wraps
import os
import numpy as np
import faiss
import json
from retrieval_system import ImageRetrievalSystem
from feature_extractor import ImageFeatureExtractor

app = Flask(__name__)

# All paths are local — index is small (few KB per product), no persistent storage needed
UPLOAD_FOLDER = "static/uploads"
INDEX_PATH = "image_index.faiss"
METADATA_PATH = "image_metadata.json"

HF_REPO_ID = "sheikh1613/ecommerce-ai-search"
HF_TOKEN = os.environ.get("HF_TOKEN", None)

# API Key for securing endpoints — set as env variable in HuggingFace Space settings
API_KEY = os.environ.get("API_KEY", "dev-key-change-me")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load existing index
retrieval_system = ImageRetrievalSystem(
    index_path=INDEX_PATH,
    metadata_path=METADATA_PATH
)

# Standalone feature extractor for adding new images
feature_extractor = ImageFeatureExtractor()


# ---- API KEY MIDDLEWARE ----
def require_api_key(f):
    """Decorator to protect endpoints with API key."""
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get("X-API-Key") or request.args.get("api_key")
        if key != API_KEY:
            return jsonify({"error": "Unauthorized. Invalid or missing API key."}), 401
        return f(*args, **kwargs)
    return decorated


def save_index_to_repo():
    """Push updated index + metadata back to HuggingFace repo (runs in background)."""
    if not HF_TOKEN:
        return
    try:
        from huggingface_hub import HfApi
        api = HfApi(token=HF_TOKEN)
        api.upload_file(
            path_or_fileobj=INDEX_PATH,
            path_in_repo=INDEX_PATH,
            repo_id=HF_REPO_ID,
            repo_type="space",
            commit_message="Auto-update FAISS index"
        )
        api.upload_file(
            path_or_fileobj=METADATA_PATH,
            path_in_repo=METADATA_PATH,
            repo_id=HF_REPO_ID,
            repo_type="space",
            commit_message="Auto-update metadata"
        )
    except Exception as e:
        print(f"Warning: Could not push index to repo: {e}")


# ---- HOME PAGE (public — test dashboard) ----
@app.route("/")
def index():
    return render_template("index.html")


# ---- SEARCH API (protected) ----
@app.route("/search", methods=["POST"])
@require_api_key
def search():
    if "image" not in request.files:
        return jsonify({"error": "No file uploaded"})

    file = request.files["image"]
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    try:
        results = retrieval_system.search(filepath)
        output = []

        for meta, score in results:
            product_id = meta.get("product_id") if isinstance(meta, dict) else None
            category = meta.get("category") if isinstance(meta, dict) else None

            output.append({
                "score": float(score),
                "product_id": product_id,
                "category": category
            })

            if len(output) == 5:
                break

        # Clean up uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)

        return jsonify({"results": output})

    except Exception as e:
        return jsonify({"error": str(e)})


# ---- ADD NEW PRODUCT IMAGE (protected) ----
@app.route("/add-image", methods=["POST"])
@require_api_key
def add_image():
    """Add a new product image to the FAISS index. Image is NOT stored — only the embedding."""
    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    product_id = request.form.get("product_id", "unknown")
    category = request.form.get("category", "uncategorized")

    # Skip if product_id already indexed (prevent duplicates)
    for key, meta in retrieval_system.metadata.items():
        if meta.get("product_id") == product_id:
            return jsonify({
                "success": True,
                "message": "Product already indexed, skipping",
                "total_images": retrieval_system.index.ntotal,
                "product_id": product_id
            })

    file = request.files["image"]

    # Save temporarily to extract features
    temp_path = os.path.join(UPLOAD_FOLDER, f"temp_{file.filename}")
    file.save(temp_path)

    try:
        # Extract features using ViT
        features = feature_extractor.extract_features(temp_path)

        # Add to FAISS index
        features_array = features.reshape(1, -1).astype(np.float32)
        retrieval_system.index.add(features_array)

        # Update metadata — only product_id and category, no image path needed
        new_idx = str(retrieval_system.index.ntotal - 1)
        retrieval_system.metadata[new_idx] = {
            "product_id": product_id,
            "category": category,
            "indexed_at": __import__("datetime").datetime.now().isoformat()
        }

        # Save index locally
        retrieval_system.save(INDEX_PATH, METADATA_PATH)

        # Clean up temp file
        os.remove(temp_path)

        return jsonify({
            "success": True,
            "message": "Image indexed successfully",
            "total_images": retrieval_system.index.ntotal,
            "product_id": product_id
        })

    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"error": str(e)}), 500


# ---- SAVE INDEX TO REPO (protected) ----
@app.route("/save", methods=["POST"])
@require_api_key
def save_to_repo():
    """Push current index + metadata to HuggingFace repo so it survives restarts."""
    try:
        save_index_to_repo()
        return jsonify({"success": True, "message": "Index saved to HuggingFace repo"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---- RESET INDEX (protected) ----
@app.route("/reset", methods=["POST"])
@require_api_key
def reset_index():
    """Clear the FAISS index and metadata. Start fresh."""
    global retrieval_system
    try:
        # Create a new empty FlatL2 index
        new_index = faiss.IndexFlatL2(feature_extractor.feature_dim)
        faiss.write_index(new_index, INDEX_PATH)

        # Clear metadata
        with open(METADATA_PATH, 'w') as f:
            json.dump({}, f)

        # Reload with empty index
        retrieval_system = ImageRetrievalSystem(
            index_path=INDEX_PATH,
            metadata_path=METADATA_PATH
        )

        return jsonify({"success": True, "message": "Index cleared", "total_images": 0})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---- GET INDEX STATS (public) ----
@app.route("/stats")
def stats():
    return jsonify({
        "total_images": retrieval_system.index.ntotal,
        "metadata_entries": len(retrieval_system.metadata)
    })


# ---- IMAGE SERVING (public) ----
@app.route("/image")
def serve_image():
    path = request.args.get("path")
    if not os.path.exists(path):
        return "Image not found", 404
    return send_file(path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860, debug=False, use_reloader=False)
