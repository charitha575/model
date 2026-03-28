# AI Visual Product Search — Project Documentation

## Project Overview

This project implements **AI-powered visual product search** for an ecommerce platform. Users can upload a photo of any product and the system finds visually similar products from the store's catalog using a Vision Transformer (ViT) model and FAISS similarity search.

**Built by:** Charitha (AI model + core search) & Sheikh (integration + deployment)

---

## Architecture

```
┌─────────────────────────────┐        ┌──────────────────────────────────┐
│  MERN Ecommerce App         │        │  AI Search Service (HuggingFace) │
│  (Render / Vercel)           │        │  (HuggingFace Spaces - FREE)     │
│                              │        │                                  │
│  Admin adds product ────────────────> │  POST /add-image                 │
│    → saves to MongoDB        │        │    → ViT extracts 768-dim embed  │
│    → sends image to AI       │        │    → Adds to FAISS index         │
│                              │        │    → Saves product_id in metadata│
│                              │        │                                  │
│  Customer uploads photo ────────────> │  POST /search                    │
│    → sends to AI service     │        │    → ViT extracts query embed    │
│    → gets product_ids back   │        │    → FAISS finds nearest matches │
│    → fetches from MongoDB    │        │    → Returns product_ids + scores│
│    → displays product cards  │        │                                  │
└─────────────────────────────┘        └──────────────────────────────────┘
```

---

## AI Model Details

| Component | Details |
|-----------|---------|
| **Model** | Vision Transformer B/16 (ViT-B/16) |
| **File** | `vit_model.pth` (327 MB) |
| **Training** | Trained on 18K ecommerce product images (9 categories) |
| **Dataset** | [Kaggle: ecommerce-product-images-18k](https://www.kaggle.com/datasets/fatihkgg/ecommerce-product-images-18k) |
| **Categories** | Baby Products, Beauty & Health, Clothing, Electronics, Grocery, Hobby & Arts, Home & Kitchen, Pet Supplies, Sports & Outdoor |
| **Embedding** | 768-dimensional vector per image |
| **Similarity** | FAISS (Facebook AI Similarity Search) with L2 distance |
| **Framework** | PyTorch + torchvision |

### How It Works

1. **Feature Extraction:** ViT-B/16 processes image (224x224) → outputs 768-dim CLS token embedding → L2 normalized
2. **Indexing:** Each product image embedding is stored in a FAISS index with its product_id
3. **Search:** Query image → extract embedding → FAISS finds k-nearest neighbors → returns product_ids with distance scores

---

## Files & Structure

```
ecommerce-ai-search/
├── app.py                    # Flask API server (main entry point)
├── feature_extractor.py      # ViT model loading + feature extraction
├── retrieval_system.py       # FAISS index management (index, search, save, load)
├── index_and_retrieve.py     # CLI tool for batch indexing + searching
├── train_vit.py              # ViT training script (used by Charitha, not needed at runtime)
├── vit_model.pth             # Trained ViT model weights (327MB) — GET FROM CHARITHA
├── image_index.faiss         # FAISS index file — GET FROM CHARITHA or build fresh
├── image_metadata.json       # Maps FAISS index positions to product info
├── templates/
│   └── index.html            # Test dashboard UI
├── static/
│   ├── style.css
│   ├── script.js
│   └── uploads/              # Temporary upload folder for search queries
├── query_images/             # Sample test images
│   ├── shoe.jpeg
│   ├── bagimages.jpg
│   └── top.webp
├── hf-space/                 # HuggingFace Spaces deployment files
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── README.md
│   └── (all app files copied here)
└── PROJECT_DOCS.md           # This file
```

---

## API Endpoints

### `POST /search` — Find similar products
```bash
curl -X POST https://your-space.hf.space/search \
  -F "image=@photo.jpg"
```
**Response:**
```json
{
  "results": [
    { "image": "/image?path=...", "score": 0.45 },
    { "image": "/image?path=...", "score": 0.67 }
  ]
}
```

### `POST /add-image` — Add product to index
```bash
curl -X POST https://your-space.hf.space/add-image \
  -F "image=@product.jpg" \
  -F "product_id=mongo_id_here" \
  -F "category=FOOTWEAR"
```
**Response:**
```json
{
  "success": true,
  "message": "Image indexed successfully",
  "total_images": 5,
  "product_id": "mongo_id_here"
}
```

### `POST /reset` — Clear index (start fresh)
```bash
curl -X POST https://your-space.hf.space/reset
```

### `POST /reindex` — Rebuild index from product_images folder
```bash
curl -X POST https://your-space.hf.space/reindex \
  -H "Content-Type: application/json" \
  -d '{"image_dir": "product_images"}'
```

### `GET /stats` — Get index info
```bash
curl https://your-space.hf.space/stats
```
**Response:**
```json
{ "total_images": 12, "metadata_entries": 12 }
```

### `GET /image?path=...` — Serve product image

---

## Deployment

### HuggingFace Spaces (AI Search Service) — FREE

**Live URL:** https://huggingface.co/spaces/sheikh1613/ecommerce-ai-search

**What's deployed:**
- Flask app + ViT model + FAISS index
- Docker-based deployment
- Port: 7860

**Storage:**
- NO persistent storage needed
- NO product images stored on HuggingFace
- FAISS index + metadata live in the repo itself (tiny: ~3KB per product)
- Images are uploaded temporarily for feature extraction, then deleted
- Only the 768-dim embedding vector is kept in FAISS

**Limits (free tier):**
- 16GB RAM (enough for 327MB model + PyTorch)
- 50GB repo storage
- Sleeps after 48h inactivity, wakes on request

### Ecommerce App (MERN) — Render/Vercel FREE

**Planned:** [mohamedsamara/mern-ecommerce](https://github.com/mohamedsamara/mern-ecommerce)
- MongoDB Atlas (free 512MB)
- Express + React
- Deploy on Render free tier

---

## Ecommerce Integration Guide

### When Admin Adds a Product (Express backend)

```javascript
// In your product controller, after saving to MongoDB:
const savedProduct = await Product.create({ name, price, image, category });

// Send image to AI service for indexing
const formData = new FormData();
formData.append("image", imageFile);
formData.append("product_id", savedProduct._id.toString());
formData.append("category", savedProduct.category);

await axios.post("https://sheikh1613-ecommerce-ai-search.hf.space/add-image", formData);
```

### When Customer Searches by Image (Express backend)

```javascript
// New route: POST /api/search/visual
const formData = new FormData();
formData.append("image", req.file.buffer, { filename: req.file.originalname });

const aiResponse = await axios.post(
  "https://sheikh1613-ecommerce-ai-search.hf.space/search",
  formData
);

// Extract product_ids from results
const productIds = aiResponse.data.results.map(r => {
  // Parse product_id from metadata
  return r.product_id;
});

// Fetch full product details from MongoDB
const products = await Product.find({ _id: { $in: productIds } });
res.json(products);
```

### Frontend — Search by Image Button (React)

```jsx
const handleImageSearch = async (e) => {
  const file = e.target.files[0];
  const formData = new FormData();
  formData.append("image", file);

  const { data } = await axios.post("/api/search/visual", formData);
  setSearchResults(data); // Display matching products
};
```

---

## Important Notes

1. **Model is already trained** — `vit_model.pth` does NOT need retraining. It works on any product image.
2. **Dataset not needed at runtime** — The Kaggle dataset (18K images) was only for training the ViT model. Don't deploy it anywhere.
3. **FAISS index is lightweight** — ~3KB per product. 1000 products = ~3MB index. Lives in the HF repo itself.
4. **NO images stored on HuggingFace** — Images are uploaded temporarily, ViT extracts the 768-dim embedding, image is deleted. Only the embedding stays in FAISS. Actual product images live in your ecommerce app's storage (Cloudinary/S3/MongoDB).
5. **NO persistent storage needed** — Index + metadata are part of the HF repo. No `/data` volume or extra storage required.
6. **Dynamic indexing works** — New products are added to FAISS on the fly via `/add-image`. No retraining needed.
7. **IndexFlatL2 vs IndexIVFFlat** — We use `IndexFlatL2` (supports adding single images without retraining). For 1000+ products, consider switching to `IndexIVFFlat` with periodic reindexing for faster search.

---

## Dependencies

```
flask==3.1.3
torch
torchvision
faiss-cpu
pillow
numpy
gunicorn
```

## Local Development

```bash
# Install dependencies
pip install flask torch torchvision faiss-cpu pillow numpy

# Run the app
python app.py
# Opens at http://127.0.0.1:5000

# To index images from a folder (CLI)
python index_and_retrieve.py
# Edit TASK, IMAGE_DIR, QUERY_IMAGE variables in the file
```

---

## Git & GitHub

**Charitha's model repo:** https://github.com/charitha575/model.git

**`.gitignore` should contain:**
```
vit_model.pth
*.faiss
__pycache__/
static/uploads/
product_images/
dataset/
```

These files are too large for GitHub. Share via Google Drive/WhatsApp.

---

## Future Improvements

- [ ] Integrate with MERN ecommerce (mohamedsamara/mern-ecommerce)
- [ ] Add "Search by Image" button to React frontend
- [ ] Auto-index on product upload from admin panel
- [ ] Add product_id to search results (currently returns image paths)
- [ ] Enable persistent storage on HuggingFace Spaces
- [ ] Add text + image combined search
- [ ] Implement product recommendations ("similar products" section)
