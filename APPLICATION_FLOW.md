# APNA Store - Complete Application Flow

## How It All Works

APNA Store is a full-stack ecommerce platform where customers can shop for products just like any online store — browse by category, search by name, add to cart, and place orders. But what makes it special is the **AI-powered visual search**. Instead of typing what you're looking for, you can simply upload a photo of a product (say, a shoe you saw someone wearing), and the AI finds visually similar products from our store. Behind the scenes, when an admin adds a new product, the product image gets uploaded to Cloudinary for display, saved to MongoDB for data, and simultaneously sent to our AI service on HuggingFace where a Vision Transformer model converts it into a 768-number fingerprint and stores it in a FAISS index. When a customer uploads a search image, the same model creates a fingerprint and FAISS instantly finds the closest matching products. The matching product IDs come back to our Express backend, which fetches the full product details from MongoDB and shows them to the customer with confidence percentages — all in about 2-3 seconds. The entire system runs on free tiers: Render for the ecommerce app, MongoDB Atlas for the database, Cloudinary for images, and HuggingFace Spaces for the AI engine.

---

## Table of Contents
1. [System Overview](#system-overview)
2. [User Authentication Flow](#1-user-authentication-flow)
3. [Admin - Category & Brand Management](#2-admin---category--brand-management)
4. [Admin - Add Product Flow](#3-admin---add-product-flow)
5. [Customer - Browse & Shop Flow](#4-customer---browse--shop-flow)
6. [Customer - AI Visual Search Flow](#5-customer---ai-visual-search-flow)
7. [Cart & Checkout Flow](#6-cart--checkout-flow)
8. [Admin - Delete Product Flow](#7-admin---delete-product-flow)
9. [Complete System Diagram](#8-complete-system-diagram)

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           APNA STORE ECOSYSTEM                             │
│                                                                             │
│  ┌──────────┐     ┌──────────────┐     ┌────────────┐     ┌──────────────┐ │
│  │  React   │────>│   Express    │────>│  MongoDB   │     │  Cloudinary  │ │
│  │ Frontend │<────│   Backend    │<────│   Atlas    │     │  (Images)    │ │
│  │ :8080    │     │   :3000      │     │            │     │              │ │
│  └──────────┘     └──────┬───────┘     └────────────┘     └──────────────┘ │
│                          │                                                  │
│                          │ HTTP (POST /search, /add-image)                  │
│                          ▼                                                  │
│                   ┌──────────────┐                                          │
│                   │ HuggingFace  │                                          │
│                   │ AI Service   │                                          │
│                   │ (ViT+FAISS)  │                                          │
│                   └──────────────┘                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. User Authentication Flow

### Login

```
User enters email & password on Login page
        │
        ▼
React Frontend ──POST /api/auth/login──> Express Backend
        │                                       │
        │                                       ▼
        │                              MongoDB: Find user by email
        │                                       │
        │                                       ▼
        │                              bcrypt.compare(password, hashedPassword)
        │                                       │
        │                              ┌────────┴────────┐
        │                              │                  │
        │                           MATCH             NO MATCH
        │                              │                  │
        │                              ▼                  ▼
        │                       Generate JWT        Return 401
        │                       token (7 days)      "Invalid credentials"
        │                              │
        │◄─────── { token, user } ─────┘
        │
        ▼
Store token in localStorage
Redirect to Dashboard
```

### Registration

```
User fills registration form (firstName, lastName, email, password)
        │
        ▼
React Frontend ──POST /api/auth/register──> Express Backend
        │                                          │
        │                                          ▼
        │                                 MongoDB: Check if email exists
        │                                          │
        │                                 ┌────────┴────────┐
        │                                 │                  │
        │                              NEW USER         EXISTS
        │                                 │                  │
        │                                 ▼                  ▼
        │                          bcrypt.hash(password)   Return 400
        │                          salt rounds: 10         "Email in use"
        │                                 │
        │                                 ▼
        │                          Save to MongoDB:
        │                          { email, hashedPassword,
        │                            firstName, lastName,
        │                            role: "ROLE MEMBER" }
        │                                 │
        │◄──── { success, token, user } ──┘
        │
        ▼
Auto-login & redirect to homepage
```

---

## 2. Admin - Category & Brand Management

### Add Category

```
Admin fills category form (name, description)
        │
        ▼
React ──POST /api/category/add──> Express Backend (auth + admin role check)
        │                                │
        │                                ▼
        │                       MongoDB: Save category
        │                       {
        │                         name: "Footwear",
        │                         slug: "footwear" (auto-generated),
        │                         description: "Shoes and sandals",
        │                         isActive: true,
        │                         products: []    ◄── empty, filled when products added
        │                       }
        │                                │
        │◄───── { success, category } ───┘
        │
        ▼
Category appears in:
  ├── Navigation menu (hamburger drawer)
  ├── Shop page sidebar filter
  └── Product add form (category dropdown)
```

### Add Brand

```
Admin fills brand form (name, description)
        │
        ▼
React ──POST /api/brand/add──> Express Backend (auth + admin role check)
        │                             │
        │                             ▼
        │                    MongoDB: Save brand
        │                    {
        │                      name: "Nike",
        │                      slug: "nike",
        │                      description: "Sportswear brand",
        │                      isActive: true
        │                    }
        │                             │
        │◄──── { success, brand } ────┘
        │
        ▼
Brand appears in:
  ├── Navigation dropdown (Brands menu)
  ├── Shop page brand filter
  └── Product add form (brand dropdown)
```

---

## 3. Admin - Add Product Flow

This is the most complex flow — involves MongoDB, Cloudinary, AND HuggingFace AI.

```
Admin fills product form:
  ├── SKU: "nike-air-001"
  ├── Name: "Nike Air Max"
  ├── Description: "Running shoes"
  ├── Price: 4999
  ├── Quantity: 50
  ├── Brand: Nike (dropdown)
  ├── Taxable: Yes
  ├── Image: shoe.jpg (file upload)
  └── Active: Yes
        │
        ▼
Click "Add Product" button
        │
        ▼
[FRONTEND] Shows loader: "Adding Product..."
           Button disabled to prevent double submit
        │
        ▼
React ──POST /api/product/add (multipart form)──> Express Backend
                                                         │
                                                         ▼
                                                  Validate all fields
                                                  (SKU unique? Name? Price?)
                                                         │
                                                         ▼
                                          ┌──────────────┴──────────────┐
                                          │                              │
                                    STEP 1: IMAGE                  STEP 2: DATABASE
                                    Upload to Cloudinary           (waits for Step 1)
                                          │                              │
                                          ▼                              │
                                   Cloudinary API:                       │
                                   Convert image to                      │
                                   base64 data URI                       │
                                          │                              │
                                          ▼                              │
                                   Upload to cloud:                      │
                                   folder: "ecommerce"                   │
                                          │                              │
                                          ▼                              │
                                   Returns:                              │
                                   imageUrl: "https://res.               │
                                     cloudinary.com/..."                 │
                                   imageKey: "ecommerce/                 │
                                     wp2omggz..."                        │
                                          │                              │
                                          └──────────┬───────────────────┘
                                                     │
                                                     ▼
                                              MongoDB: Save product
                                              {
                                                sku: "nike-air-001",
                                                name: "Nike Air Max",
                                                slug: "nike-air-max" (auto),
                                                description: "Running shoes",
                                                price: 4999,
                                                quantity: 50,
                                                brand: ObjectId("..."),
                                                imageUrl: "https://res.cloudinary...",
                                                imageKey: "ecommerce/wp2omggz...",
                                                isActive: true
                                              }
                                                     │
                                                     ▼
                                              Product saved! _id = "69c6a6b3..."
                                                     │
                                                     ▼
                                          ┌──────────┴──────────┐
                                          │   STEP 3: AI INDEX   │
                                          │   (runs after save)  │
                                          └──────────┬──────────┘
                                                     │
                                                     ▼
                                              Create FormData:
                                              ├── image: shoe.jpg (buffer)
                                              ├── product_id: "69c6a6b3..."
                                              └── category: "Nike Air Max"
                                                     │
                                                     ▼
                                              POST to HuggingFace:
                                              https://charitha986-commerce-
                                              ai-searching.hf.space/add-image
                                              Headers:
                                              ├── Authorization: Bearer <HF_TOKEN>
                                              └── X-API-Key: <API_KEY>
                                                     │
                                                     ▼
                                              ┌──────────────────────────┐
                                              │   HuggingFace AI Service  │
                                              │                          │
                                              │  1. Receive image        │
                                              │  2. ViT-B/16 extracts   │
                                              │     768-dim embedding    │
                                              │  3. Add to FAISS index   │
                                              │  4. Save metadata:       │
                                              │     idx → product_id     │
                                              │  5. Delete temp image    │
                                              │  6. Return success       │
                                              └──────────────────────────┘
                                                     │
                                                     ▼
                                              { success: true,
                                                total_images: 5,
                                                product_id: "69c6a6b3..." }
                                                     │
                                    ◄────────────────┘
                                    │
                                    ▼
                             [FRONTEND]
                             ├── Hide loader
                             ├── Show success notification
                             ├── Reset form
                             └── Redirect to product list

NOTE: If AI indexing fails, the product is STILL saved
      (Cloudinary + MongoDB). Visual search just won't
      find it until re-indexed. This is by design — we
      don't want AI failures to block product creation.
```

---

## 4. Customer - Browse & Shop Flow

### Text Search (Auto-Suggest)

```
Customer types "nike" in search bar
        │
        ▼
Every 3 characters typed, React fires:
GET /api/product/list/search/nike
        │
        ▼
Express Backend:
  MongoDB.find({ name: /nike/i, isActive: true })
        │
        ▼
Returns matching products with name, slug, imageUrl, price
        │
        ▼
[FRONTEND] Shows dropdown with product suggestions
           Each shows: image + name + price
        │
        ▼
Customer clicks a suggestion
        │
        ▼
Navigate to /product/nike-air-max (product page)
```

### Browse by Category

```
Customer clicks "Footwear" in sidebar
        │
        ▼
Navigate to /shop/category/footwear
        │
        ▼
React ──GET /api/product/list?category=footwear──> Express Backend
        │                                                 │
        │                                                 ▼
        │                                        MongoDB: Find category
        │                                        by slug "footwear"
        │                                                 │
        │                                                 ▼
        │                                        Get all product IDs
        │                                        in that category
        │                                                 │
        │                                                 ▼
        │                                        Fetch products with
        │                                        filters (price, rating,
        │                                        sort, pagination)
        │                                                 │
        │◄──── { products, totalPages, count } ───────────┘
        │
        ▼
[FRONTEND] Display product grid with:
  ├── Product image (from Cloudinary URL)
  ├── Product name
  ├── Price in ₹
  ├── Rating stars
  └── Pagination controls
```

---

## 5. Customer - AI Visual Search Flow

This is the core AI feature of the application.

```
Customer clicks camera icon (next to search bar)
        │
        ▼
Visual Search Modal opens
        │
        ▼
Customer uploads a product image (e.g., photo of a shoe)
        │
        ▼
[FRONTEND]
  ├── Show image preview under "YOUR IMAGE"
  ├── Show spinner: "Analyzing image with AI..."
  └── Send image to backend
        │
        ▼
React ──POST /api/product/visual-search (multipart)──> Express Backend
                                                              │
                                                              ▼
                                                       Create FormData:
                                                       └── image: uploaded file buffer
                                                              │
                                                              ▼
                                                       POST to HuggingFace:
                                                       https://charitha986-commerce-
                                                       ai-searching.hf.space/search
                                                       Headers:
                                                       ├── Authorization: Bearer <HF_TOKEN>
                                                       └── X-API-Key: <API_KEY>
                                                              │
                                                              ▼
                                                 ┌────────────────────────────┐
                                                 │    HuggingFace AI Service   │
                                                 │                            │
                                                 │  1. Receive query image    │
                                                 │  2. Save temporarily       │
                                                 │  3. ViT-B/16 extracts     │
                                                 │     768-dim embedding      │
                                                 │  4. FAISS searches for     │
                                                 │     nearest neighbors      │
                                                 │     (L2 distance)          │
                                                 │  5. Delete temp image      │
                                                 │  6. Return top matches:    │
                                                 │     [                      │
                                                 │       {                    │
                                                 │         product_id: "69c6..│
                                                 │         category: "shoe",  │
                                                 │         score: 0.45        │
                                                 │       },                   │
                                                 │       ...                  │
                                                 │     ]                      │
                                                 └────────────────────────────┘
                                                              │
                                                              ▼
                                                       Express receives AI results
                                                              │
                                                              ▼
                                                       Filter results:
                                                       ├── Only valid MongoDB ObjectIds
                                                       ├── Calculate confidence:
                                                       │   confidence = 1/(1+score) * 100
                                                       ├── Keep only > 50% confidence
                                                       ├── Sort by highest confidence first
                                                       └── Limit to top 5 results
                                                              │
                                                              ▼
                                                       MongoDB: Fetch full product details
                                                       Product.find({
                                                         _id: { $in: [product_ids] },
                                                         isActive: true
                                                       }).populate('brand')
                                                              │
                                                              ▼
                                                       Attach confidence scores to products
                                                              │
                                    ◄─────────────────────────┘
                                    │
                                    ▼
                             [FRONTEND] Display results in modal:
                             ┌──────────────────────────────────┐
                             │  #1  [Image] Nike Air Max        │
                             │              ₹4999               │
                             │              Nike                │
                             │              [92.3%] match       │ ◄── green badge
                             ├──────────────────────────────────┤
                             │  #2  [Image] Puma Runner          │
                             │              ₹3499               │
                             │              Puma                │
                             │              [78.5%] match       │ ◄── yellow badge
                             ├──────────────────────────────────┤
                             │  #3  [Image] Woodland Leather    │
                             │              ₹5999               │
                             │              Woodland            │
                             │              [61.2%] match       │ ◄── yellow badge
                             └──────────────────────────────────┘

                             Match badge colors:
                             ├── Green:  80% and above
                             ├── Yellow: 50% - 79%
                             └── Red:    below 50% (filtered out, not shown)

                             Customer clicks a result
                                    │
                                    ▼
                             Modal closes → Navigate to product page
```

---

## 6. Cart & Checkout Flow

```
Customer clicks "Add to Bag" on product page
        │
        ▼
React ──POST /api/cart/add──> Express Backend (auth required)
        │                            │
        │                            ▼
        │                   MongoDB: Add to cart
        │                   {
        │                     user: ObjectId("user_id"),
        │                     products: [{
        │                       product: ObjectId("product_id"),
        │                       quantity: 1
        │                     }]
        │                   }
        │                            │
        │◄──── { success, cart } ────┘
        │
        ▼
Cart icon updates with item count
        │
        ▼
Customer opens cart drawer (clicks cart icon)
        │
        ▼
Shows cart items with:
├── Product image (Cloudinary URL)
├── Product name
├── Price in ₹
├── Quantity selector
└── Total
        │
        ▼
Customer clicks "Checkout"
        │
        ▼
POST /api/order/add
        │
        ▼
MongoDB: Create order
{
  user: ObjectId("user_id"),
  products: [...],
  total: 4999,
  status: "Not processed"
}
        │
        ▼
Order confirmation page
```

---

## 7. Admin - Delete Product Flow

```
Admin clicks "Delete" on product in dashboard
        │
        ▼
React ──DELETE /api/product/delete/:id──> Express Backend
        │                                        │
        │                                        ▼
        │                               MongoDB: Find product
        │                               Get imageKey for Cloudinary
        │                                        │
        │                                        ▼
        │                               ┌────────┴────────┐
        │                               │                  │
        │                        Cloudinary:           MongoDB:
        │                        Delete image          Delete product
        │                        by imageKey           document
        │                               │                  │
        │                               └────────┬─────────┘
        │                                        │
        │◄───── { success } ─────────────────────┘
        │
        ▼
Product removed from list

NOTE: The FAISS index entry on HuggingFace is NOT deleted.
This is harmless — when visual search returns this product_id,
MongoDB won't find it (deleted), so it's never shown to users.
The orphaned FAISS entry wastes ~3KB and doesn't affect accuracy.
```

---

## 8. Complete System Diagram

```
                              ┌─────────────────┐
                              │    CUSTOMER      │
                              │    BROWSER       │
                              └────────┬────────┘
                                       │
                          ┌────────────┼────────────┐
                          │            │            │
                     Text Search   Browse     Visual Search
                          │         Shop      (Camera Icon)
                          │            │            │
                          ▼            ▼            ▼
              ┌──────────────────────────────────────────────┐
              │              REACT FRONTEND                   │
              │              (Render / :8080)                  │
              │                                               │
              │  ┌──────────┐ ┌──────────┐ ┌───────────────┐ │
              │  │ Search   │ │ Product  │ │ Visual Search │ │
              │  │ Bar      │ │ Grid     │ │ Modal         │ │
              │  │ (auto-   │ │ (cards   │ │ (upload image │ │
              │  │ suggest) │ │ + filter)│ │ → results)    │ │
              │  └──────────┘ └──────────┘ └───────────────┘ │
              └───────────────────┬───────────────────────────┘
                                  │
                          All API calls go to
                          /api/* endpoints
                                  │
                                  ▼
              ┌──────────────────────────────────────────────┐
              │            EXPRESS BACKEND                    │
              │            (Render / :3000)                   │
              │                                               │
              │  ┌─────────────────────────────────────────┐ │
              │  │              API ROUTES                  │ │
              │  │                                         │ │
              │  │  /auth     → login, register, password  │ │
              │  │  /product  → CRUD + visual-search       │ │
              │  │  /cart     → add, remove                 │ │
              │  │  /order    → place, list, status         │ │
              │  │  /brand    → CRUD                        │ │
              │  │  /category → CRUD                        │ │
              │  │  /review   → add, approve                │ │
              │  └─────────────────────────────────────────┘ │
              │                    │                          │
              │         ┌─────────┼─────────┐                │
              │         │         │         │                │
              │         ▼         ▼         ▼                │
              │  ┌──────────┐ ┌──────┐ ┌──────────┐         │
              │  │ MongoDB  │ │Cloud-│ │HuggingFace│         │
              │  │ Atlas    │ │inary │ │AI Service │         │
              │  └──────────┘ └──────┘ └──────────┘         │
              └──────────────────────────────────────────────┘
                      │            │           │
                      ▼            ▼           ▼
              ┌──────────┐  ┌──────────┐ ┌──────────────────┐
              │ MongoDB  │  │Cloudinary│ │  HuggingFace     │
              │ Atlas    │  │   CDN    │ │  Spaces          │
              │          │  │          │ │                   │
              │ Stores:  │  │ Stores:  │ │ Stores:          │
              │ • Users  │  │ • Product│ │ • ViT model      │
              │ • Products│ │   images │ │   (327MB)        │
              │ • Orders │  │          │ │ • FAISS index    │
              │ • Cart   │  │ Returns: │ │   (embeddings)   │
              │ • Brands │  │ • CDN URL│ │ • Metadata       │
              │ • Reviews│  │   for    │ │   (product_id    │
              │ • etc.   │  │   display│ │    mapping)      │
              └──────────┘  └──────────┘ └──────────────────┘

              Free Tier       Free Tier      Free Tier
              512MB storage   25GB           16GB RAM
                              bandwidth      CPU Basic
```

---

## Data Storage Summary

| Data | Storage | Purpose |
|------|---------|---------|
| User accounts, passwords | MongoDB Atlas | Authentication |
| Product info (name, price, SKU) | MongoDB Atlas | Product catalog |
| Product images (visual display) | Cloudinary CDN | Fast image delivery |
| Categories & Brands | MongoDB Atlas | Product organization |
| Orders & Cart | MongoDB Atlas | Shopping flow |
| Reviews & Ratings | MongoDB Atlas | Social proof |
| Image embeddings (768 numbers per product) | HuggingFace FAISS | AI visual search |
| ViT model weights (327MB) | HuggingFace Space | Feature extraction |
| Product ID ↔ FAISS index mapping | HuggingFace metadata JSON | Link AI results to products |

---

## Security Flow

```
Every API request:
        │
        ├── Public routes (no auth needed):
        │   ├── GET /api/product/list
        │   ├── GET /api/product/item/:slug
        │   ├── POST /api/auth/login
        │   ├── POST /api/auth/register
        │   └── POST /api/product/visual-search
        │
        └── Protected routes (JWT token required):
            │
            ▼
            Check Authorization header
            jwt.verify(token, SECRET_KEY)
                │
                ├── Valid → Extract user from token
                │           │
                │           ├── ROLE MEMBER → cart, orders, reviews, wishlist
                │           ├── ROLE MERCHANT → own brand products + member routes
                │           └── ROLE ADMIN → everything (users, all products, all orders)
                │
                └── Invalid/Expired → Return 401 Unauthorized

HuggingFace API Security:
        │
        ├── Layer 1: Private Space (HuggingFace Bearer token)
        │   Only requests with valid HF_TOKEN can reach the Space
        │
        └── Layer 2: API Key (X-API-Key header)
            Must match the API_KEY secret set in the Space
```
