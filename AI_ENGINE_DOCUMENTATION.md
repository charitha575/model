# AI Visual Search Engine - Technical Documentation

## Overview

The AI Visual Search Engine is a deep learning-based image retrieval system that enables users to search for products by uploading an image. The system finds visually similar products from the store's catalog using a Vision Transformer (ViT) model and Facebook AI Similarity Search (FAISS).

---

## Architecture

```
User uploads image
       |
       v
ViT-B/16 Model (Pre-trained on ecommerce product images)
       |
       v
768-dimensional feature vector (embedding)
       |
       v
FAISS Index (similarity search)
       |
       v
Top-K similar products returned (with confidence scores)
```

---

## Model Details

| Component | Specification |
|-----------|--------------|
| **Model Architecture** | Vision Transformer B/16 (ViT-B/16) |
| **Model File** | `vit_model.pth` (327 MB) |
| **Input Size** | 224 x 224 pixels (RGB) |
| **Output** | 768-dimensional embedding vector |
| **Training Dataset** | [Ecommerce Product Images 18K](https://www.kaggle.com/datasets/fatihkgg/ecommerce-product-images-18k) |
| **Total Training Images** | 18,175 images |
| **Number of Classes** | 9 product categories |
| **Framework** | PyTorch + torchvision |

### Product Categories (Training Data)

1. Baby Products
2. Beauty & Health
3. Clothing, Accessories & Jewellery
4. Electronics
5. Grocery
6. Hobby, Arts & Stationery
7. Home, Kitchen & Tools
8. Pet Supplies
9. Sports & Outdoor

---

## How It Works

### 1. Feature Extraction (`feature_extractor.py`)

The `ImageFeatureExtractor` class handles converting product images into numerical vectors:

- **Preprocessing**: Images are resized to 224x224, center-cropped, converted to tensors, and normalized using ImageNet statistics (mean: [0.485, 0.456, 0.406], std: [0.229, 0.224, 0.225])
- **Model Loading**: Loads custom-trained ViT-B/16 weights from `vit_model.pth`. The classification head (trained for 8 classes) is replaced with `nn.Identity()` to extract the CLS token embedding
- **Embedding Generation**: Forward pass through the model produces a 768-dimensional vector representing the image's visual features
- **Normalization**: L2 normalization is applied to the feature vector for consistent similarity comparison

### 2. Indexing (`retrieval_system.py`)

The `ImageRetrievalSystem` class manages the FAISS index:

- **Index Type**: `IndexFlatL2` — exact L2 distance search, supports dynamic addition of vectors without retraining
- **Storage**: Each product image is stored as a 768-float vector (~3KB per product)
- **Metadata**: JSON mapping from FAISS index position to product_id and category
- **Persistence**: Index saved as `image_index.faiss`, metadata as `image_metadata.json`

### 3. Search Process

```
1. Query image received
2. ViT extracts 768-dim embedding from query image
3. FAISS computes L2 distance between query and all indexed vectors
4. Top-K nearest neighbors returned
5. Results sorted by distance (lower = more similar)
6. Product IDs returned to the ecommerce application
```

### 4. Similarity Scoring

- **Distance Metric**: L2 (Euclidean) distance between normalized vectors
- **Score 0.0**: Identical image (exact match)
- **Score < 1.0**: Very similar products
- **Score 1.0 - 2.0**: Moderately similar
- **Score > 2.0**: Weak similarity
- **Confidence Display**: Converted to percentage using `1 / (1 + distance) * 100`

---

## API Endpoints

### `POST /search` (Protected)

Find similar products by uploading an image.

**Headers:**
- `Authorization: Bearer <HF_TOKEN>` (HuggingFace auth for private space)
- `X-API-Key: <API_KEY>` (application-level security)

**Request:** Multipart form data with `image` field

**Response:**
```json
{
  "results": [
    {
      "product_id": "69c6a6b36e1c245ac01a7cb9",
      "category": "FOOTWEAR",
      "score": 0.45
    }
  ]
}
```

### `POST /add-image` (Protected)

Index a new product image for visual search.

**Form Fields:**
- `image` — product image file
- `product_id` — MongoDB ObjectId of the product
- `category` — product category name

**Response:**
```json
{
  "success": true,
  "message": "Image indexed successfully",
  "total_images": 15,
  "product_id": "69c6a6b36e1c245ac01a7cb9"
}
```

### `POST /reset` (Protected)

Clear the entire FAISS index and start fresh.

### `GET /stats` (Public)

Returns total indexed images and metadata count.

---

## File Structure

```
ai-search/
├── app.py                    # Flask API server (port 7860)
├── feature_extractor.py      # ViT model loading + feature extraction
├── retrieval_system.py       # FAISS index management (index, search, save, load)
├── index_and_retrieve.py     # CLI tool for batch indexing + searching
├── train_vit.py              # ViT training script (used once for training)
├── vit_model.pth             # Trained ViT model weights (327MB)
├── image_index.faiss         # FAISS index file
├── image_metadata.json       # Product ID to index position mapping
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker build configuration
├── templates/
│   └── index.html            # Test dashboard UI
└── static/
    ├── style.css
    └── script.js
```

---

## Deployment

**Platform:** HuggingFace Spaces (Docker SDK, CPU Basic - Free Tier)

**URL:** `https://charitha986-commerce-ai-searching.hf.space`

**Resources:**
- 16GB RAM (free tier)
- CPU Basic
- 50GB storage
- Sleeps after 48h inactivity, wakes on request

**Docker Build Caching:**
- PyTorch and dependencies are cached in the Docker layer
- Code-only changes rebuild in under 1 minute
- Full rebuild (requirements change) takes ~10 minutes

**Security:**
- Space is private (requires HuggingFace Bearer token)
- All write endpoints protected with X-API-Key header
- Images are temporarily uploaded for feature extraction, then deleted
- Only 768-number embeddings are stored, not actual images

---

## Performance

| Metric | Value |
|--------|-------|
| Feature extraction time | ~0.5s per image (CPU) |
| Search time (100 products) | ~1ms |
| Search time (10,000 products) | ~5ms |
| Index size per product | ~3KB |
| Model load time | ~5-10s (cold start) |
| Total memory usage | ~800MB (model + PyTorch + FAISS) |

---

## Limitations

1. **CPU-only inference** — GPU would be 10x faster but requires paid tier
2. **Cold start** — If the Space sleeps (48h inactivity), first request takes ~30s to wake up
3. **Single index** — All products in one flat index; for 10,000+ products, should switch to IndexIVFFlat with periodic reindexing
4. **No text search** — Only visual (image-to-image) search; text queries not supported
5. **Training bias** — Model trained on 9 categories; accuracy may vary for products outside these categories

---

## Future Improvements

- GPU acceleration for faster inference
- Text + image combined search (multimodal)
- Product recommendations based on browsing history
- Automatic reindexing when products are deleted
- ONNX model conversion for faster CPU inference
