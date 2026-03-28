# AI Search Integration with Ecommerce - Technical Documentation

## Overview

This document describes how the AI Visual Search Engine is integrated with the APNA Store ecommerce platform. The integration enables customers to search for products by uploading an image, and automatically indexes product images when admins add new products.

---

## System Architecture

```
┌────────────────────────────────────────┐     ┌────────────────────────────────────────┐
│         APNA Store (MERN)              │     │      AI Search Service                 │
│         Render (Free Tier)             │     │      HuggingFace Spaces (Free)         │
│                                        │     │                                        │
│  React Frontend (port 8080)            │     │  Flask API (port 7860)                 │
│  ├── Visual Search Modal               │     │  ├── ViT-B/16 Model (327MB)            │
│  ├── Camera button in navbar           │     │  ├── FAISS Index                       │
│  └── Product cards with match %        │     │  ├── POST /search                      │
│                                        │     │  ├── POST /add-image                   │
│  Express Backend (port 3000)           │     │  └── POST /reset                       │
│  ├── POST /api/product/visual-search   │────>│                                        │
│  ├── POST /api/product/add (auto-index)│────>│  Security:                             │
│  ├── MongoDB Atlas                     │     │  ├── Private Space (HF Bearer token)   │
│  └── Cloudinary (image storage)        │     │  └── X-API-Key header                  │
└────────────────────────────────────────┘     └────────────────────────────────────────┘
```

---

## Integration Points

### 1. Admin Adds Product (Auto-Indexing)

When an admin adds a new product with an image through the dashboard:

```
Admin fills product form → clicks "Add Product"
        │
        ├── Image uploaded to Cloudinary → returns imageUrl
        │
        ├── Product saved to MongoDB (name, price, imageUrl, etc.)
        │
        └── Image sent to AI service → POST /add-image
                ├── product_id = MongoDB ObjectId
                ├── category = product name
                └── ViT extracts embedding → stored in FAISS index
```

**Backend Code** (`server/routes/api/product.js`):

```javascript
// After saving product to MongoDB
if (image) {
  const aiFormData = new FormData();
  aiFormData.append('image', image.buffer, {
    filename: image.originalname,
    contentType: image.mimetype
  });
  aiFormData.append('product_id', savedProduct._id.toString());
  aiFormData.append('category', name);

  await axios.post(`${AI_SEARCH_URL}/add-image`, aiFormData, {
    headers: {
      ...aiFormData.getHeaders(),
      'X-API-Key': AI_API_KEY,
      'Authorization': `Bearer ${HF_TOKEN}`
    },
    timeout: 30000
  });
}
```

### 2. Customer Visual Search

When a customer uploads an image through the visual search modal:

```
Customer clicks camera icon → uploads photo
        │
        ├── Frontend sends image to Express backend
        │   POST /api/product/visual-search
        │
        ├── Backend forwards image to AI service
        │   POST /search (with HF_TOKEN + API_KEY)
        │
        ├── AI returns matching product_ids with scores
        │   [{ product_id: "69c6...", score: 0.45 }]
        │
        ├── Backend fetches full product details from MongoDB
        │   Product.find({ _id: { $in: productIds } })
        │
        └── Frontend displays ranked results with match %
```

**Backend Code** (`server/routes/api/product.js`):

```javascript
router.post('/visual-search', upload.single('image'), async (req, res) => {
  // Send to AI service
  const aiResponse = await axios.post(`${AI_SEARCH_URL}/search`, formData, {
    headers: {
      ...formData.getHeaders(),
      'X-API-Key': AI_API_KEY,
      'Authorization': `Bearer ${HF_TOKEN}`
    }
  });

  // Get product IDs from AI results
  const productIds = results
    .map(r => r.product_id)
    .filter(id => Mongoose.Types.ObjectId.isValid(id));

  // Fetch full products from MongoDB
  const products = await Product.find({ _id: { $in: productIds }, isActive: true });

  // Attach confidence scores and return
  res.json({ products: productsWithScores });
});
```

### 3. Admin Deletes Product

When a product is deleted, the Cloudinary image is also removed:

```
Admin deletes product
        │
        ├── Cloudinary image deleted (using imageKey)
        └── MongoDB product removed

Note: FAISS index entry remains but is harmless —
the product_id won't match any MongoDB document,
so it's never returned to the user.
```

---

## Frontend Components

### Visual Search Modal (`client/app/components/Store/VisualSearch/index.js`)

- **Camera Button**: Circular button with camera icon placed next to the search bar in the navigation
- **Upload Area**: Drag-and-drop style upload with camera icon
- **Preview**: Shows the uploaded query image
- **Loading State**: Spinner with "Analyzing image with AI..." message
- **Results List**: Ranked list layout (not grid) sorted by highest match first
  - Each result shows: rank (#1, #2...), product image, name, price, brand, match percentage
  - Color-coded match badges: green (80%+), yellow (50-80%), red (<50%)
- **Click to Navigate**: Clicking a result closes the modal and navigates to the product page

### Add Product Loader (`client/app/components/Manager/AddProduct/index.js`)

- Shows spinner and "Uploading image & indexing for AI search..." while the product is being added
- Button disabled during upload to prevent double submission

---

## Environment Variables

### Express Backend (.env)

| Variable | Description | Example |
|----------|-------------|---------|
| `AI_SEARCH_URL` | HuggingFace Space URL | `https://charitha986-commerce-ai-searching.hf.space` |
| `AI_API_KEY` | API key for AI service authentication | `Y4pwj3lgrttP71RraXEGE51OixKeyjI_yccPbofCNeY` |
| `HF_TOKEN` | HuggingFace token for private space access | `hf_XSEa...` |

### HuggingFace Space (Secrets)

| Secret | Description |
|--------|-------------|
| `API_KEY` | Must match the `AI_API_KEY` in Express backend |

---

## Security Layers

| Layer | Mechanism | Purpose |
|-------|-----------|---------|
| **HuggingFace Space** | Private visibility | Only accessible with HF Bearer token |
| **API Endpoints** | X-API-Key header | Application-level authentication |
| **Express Backend** | JWT auth on admin routes | Only authenticated admins can add/delete products |
| **CORS** | Express CORS middleware | Restricts API access to allowed origins |

---

## Data Flow Summary

| Data | Where Stored | Why |
|------|-------------|-----|
| Product images (display) | **Cloudinary** | Fast CDN delivery, permanent storage |
| Product data (name, price) | **MongoDB Atlas** | Database queries, relationships |
| Image embeddings (search) | **FAISS on HuggingFace** | Fast similarity search, ~3KB per product |
| ViT model weights | **HuggingFace Space** | Feature extraction at runtime |

**Key Design Decision**: Product images are NOT stored on HuggingFace. Only the 768-number embedding vectors are kept in FAISS. This keeps the AI service lightweight and eliminates storage concerns.

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| AI service down/sleeping | Product still saves to MongoDB; AI indexing fails silently; visual search returns error message |
| Invalid image uploaded | Backend returns 400 with error message |
| No matching products | Frontend shows "No matching products found" |
| HuggingFace cold start | First request after 48h sleep takes ~30s; subsequent requests are fast |
| Network timeout | 30-second timeout on all AI service calls |

---

## Performance Characteristics

| Operation | Time |
|-----------|------|
| Add product (Cloudinary + MongoDB + AI index) | ~3-5 seconds |
| Visual search (upload + AI search + MongoDB lookup) | ~2-4 seconds |
| AI service cold start | ~30 seconds |
| AI service warm search | ~1-2 seconds |
