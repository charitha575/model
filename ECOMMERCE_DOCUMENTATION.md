# APNA Store - Ecommerce Platform Documentation

## Overview

APNA Store is a full-stack ecommerce platform built with the MERN stack (MongoDB, Express.js, React, Node.js). It features AI-powered visual product search, role-based access control (Admin/Merchant/Buyer), product management, shopping cart, order processing, and review system.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 16, Redux, Redux Thunk, React Router v5, Bootstrap 4, Reactstrap, Sass |
| **Backend** | Node.js, Express.js, Passport.js (JWT) |
| **Database** | MongoDB Atlas (Mongoose ODM) |
| **Image Storage** | Cloudinary |
| **AI Search** | HuggingFace Spaces (ViT + FAISS) |
| **Deployment** | Render (Web Service, Free Tier) |

---

## Features

### Customer Features
- Browse products by category, brand, price range, and rating
- **AI Visual Search** — upload a product image to find similar items
- Text-based product search with auto-suggestions
- Add products to cart and checkout
- Add products to wishlist
- Write product reviews and ratings
- Order history and tracking
- User profile management
- Password reset via email

### Admin Features
- Add, edit, and delete products (with image upload to Cloudinary)
- Automatic AI indexing of product images on upload
- Manage brands and categories
- View and manage all orders
- User management
- Review approval system

### Merchant Features
- Manage own brand products
- Product inventory management
- Order management for own products

---

## Project Structure

```
apna-store/
├── client/                          # React Frontend
│   ├── app/
│   │   ├── components/
│   │   │   ├── Common/              # Shared UI components
│   │   │   │   ├── Button/
│   │   │   │   ├── CartIcon/
│   │   │   │   ├── Footer/
│   │   │   │   ├── Input/
│   │   │   │   ├── SearchBar/
│   │   │   │   ├── SignupProvider/
│   │   │   │   └── ...
│   │   │   ├── Manager/             # Admin/Merchant dashboard components
│   │   │   │   ├── AddProduct/
│   │   │   │   ├── OrderList/
│   │   │   │   ├── ProductList/
│   │   │   │   └── ...
│   │   │   └── Store/               # Customer-facing components
│   │   │       ├── CartList/
│   │   │       ├── ProductFilter/
│   │   │       ├── ProductList/
│   │   │       ├── VisualSearch/    # AI Visual Search modal
│   │   │       └── ...
│   │   ├── containers/              # Page-level containers (connected to Redux)
│   │   │   ├── Navigation/          # Header with search bar + camera icon
│   │   │   ├── Shop/                # Shop page with category sidebar
│   │   │   ├── ProductPage/         # Single product view
│   │   │   ├── Cart/
│   │   │   ├── Dashboard/
│   │   │   ├── Login/
│   │   │   ├── Product/             # Admin product CRUD
│   │   │   └── ...
│   │   ├── styles/                  # SCSS stylesheets
│   │   │   └── core/
│   │   │       ├── _visual-search.scss
│   │   │       └── ...
│   │   └── constants/               # API URLs, roles, cart constants
│   ├── public/                      # Static assets, index.html
│   └── webpack/                     # Webpack config (dev + prod)
│
├── server/                          # Express Backend
│   ├── config/
│   │   ├── keys.js                  # Environment config (MongoDB, JWT, Cloudinary, AI)
│   │   ├── passport.js              # JWT + Google + Facebook auth strategies
│   │   └── template.js              # Email templates
│   ├── middleware/
│   │   ├── auth.js                  # JWT authentication middleware
│   │   └── role.js                  # Role-based access control
│   ├── models/                      # Mongoose schemas
│   │   ├── product.js
│   │   ├── user.js
│   │   ├── order.js
│   │   ├── brand.js
│   │   ├── category.js
│   │   ├── cart.js
│   │   ├── review.js
│   │   ├── wishlist.js
│   │   └── ...
│   ├── routes/api/                  # API endpoints
│   │   ├── product.js               # Product CRUD + visual search + AI indexing
│   │   ├── auth.js                  # Login, register, password reset
│   │   ├── cart.js
│   │   ├── order.js
│   │   ├── brand.js
│   │   ├── category.js
│   │   ├── review.js
│   │   └── ...
│   ├── utils/
│   │   ├── storage.js               # Cloudinary image upload (replaced AWS S3)
│   │   ├── db.js                    # MongoDB connection
│   │   └── seed.js                  # Database seeding script
│   └── index.js                     # Express server entry point
│
├── package.json                     # Root package (runs both client + server)
└── docker-compose.yml               # Docker setup for local development
```

---

## API Endpoints

### Authentication
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/auth/register` | Register new user | Public |
| POST | `/api/auth/login` | Login | Public |
| GET | `/api/auth/google` | Google OAuth login | Public |
| POST | `/api/auth/forgot` | Forgot password | Public |
| POST | `/api/auth/reset/:token` | Reset password | Public |

### Products
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/product/list` | List products with filters | Public |
| GET | `/api/product/item/:slug` | Get product by slug | Public |
| GET | `/api/product/list/search/:name` | Text search products | Public |
| POST | `/api/product/visual-search` | **AI visual search** | Public |
| POST | `/api/product/add` | Add product (+ Cloudinary + AI index) | Admin/Merchant |
| PUT | `/api/product/:id` | Update product | Admin/Merchant |
| DELETE | `/api/product/delete/:id` | Delete product (+ Cloudinary cleanup) | Admin/Merchant |

### Cart
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/cart/add` | Add to cart | User |
| DELETE | `/api/cart/delete/:cartId` | Remove from cart | User |

### Orders
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/order/add` | Place order | User |
| GET | `/api/order` | Get user orders | User |
| PUT | `/api/order/status/item/:itemId` | Update order status | Admin |

### Brands & Categories
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/brand/list` | List all brands | Public |
| POST | `/api/brand/add` | Add brand | Admin |
| GET | `/api/category/list` | List all categories | Public |
| POST | `/api/category/add` | Add category | Admin |

---

## Database Schema

### User
```
{
  email: String (unique),
  password: String (bcrypt hashed),
  firstName: String,
  lastName: String,
  role: "ROLE ADMIN" | "ROLE MEMBER" | "ROLE MERCHANT",
  provider: "Email" | "Google" | "Facebook",
  merchant: ObjectId (ref: Merchant)
}
```

### Product
```
{
  sku: String (unique),
  name: String,
  slug: String (auto-generated),
  description: String,
  quantity: Number,
  price: Number,
  taxable: Boolean,
  isActive: Boolean,
  brand: ObjectId (ref: Brand),
  imageUrl: String (Cloudinary URL),
  imageKey: String (Cloudinary public_id)
}
```

### Category
```
{
  name: String,
  slug: String,
  description: String,
  isActive: Boolean,
  products: [ObjectId] (ref: Product)
}
```

### Brand
```
{
  name: String,
  slug: String,
  description: String,
  isActive: Boolean,
  merchant: ObjectId (ref: Merchant)
}
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PORT` | Server port (default: 3000) |
| `MONGO_URI` | MongoDB Atlas connection string |
| `JWT_SECRET` | JWT signing secret |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret |
| `AI_SEARCH_URL` | HuggingFace Space URL for visual search |
| `AI_API_KEY` | API key for AI service authentication |
| `HF_TOKEN` | HuggingFace token for private space access |
| `CLIENT_URL` | Frontend URL (for CORS and emails) |
| `BASE_API_URL` | API base path (default: `api`) |
| `NODE_ENV` | `development` or `production` |

---

## Deployment

### Render (Web Service)

| Setting | Value |
|---------|-------|
| **Build Command** | `cd client && npm install && API_URL=/api npm run build && cd ../server && npm install` |
| **Start Command** | `node server/index.js` |
| **Instance Type** | Free |
| **Auto Deploy** | Enabled (on push to main) |

**Production URL:** `https://apna-store-uokg.onrender.com`

### How Production Serves Work

In production (`NODE_ENV=production`), Express serves:
1. API routes at `/api/*`
2. React static build from `client/dist/`
3. Catch-all `*` route serves `index.html` for React Router

---

## Customizations Made (from original mohamedsamara/mern-ecommerce)

| Change | Details |
|--------|---------|
| **Branding** | "MERN Store" → "APNA Store" across all files |
| **Currency** | USD ($) → INR (₹) in all price displays |
| **Image Storage** | AWS S3 → Cloudinary |
| **AI Visual Search** | New feature — camera button + search modal + HuggingFace integration |
| **Product Auto-Indexing** | New — products automatically indexed in AI on upload |
| **Categories in Sidebar** | Fixed — categories now show in shop page filter |
| **Indian Data** | Seeded with Indian brands (Nike, Puma, Boat, Samsung, Levi's, Woodland, Fastrack, Noise) and categories (Footwear, Electronics, Clothing, Accessories, Home & Kitchen, Sports) |
| **Removed** | Facebook login, Google login, top info bar, footer social icons, product social share |
| **Add Product Loader** | Shows spinner while uploading image and indexing |
| **Product Deletion** | Now also deletes image from Cloudinary |
| **DNS Fix** | Google DNS (8.8.8.8) for MongoDB Atlas SRV resolution on restricted networks |

---

## Seeded Data

### Admin Account
- **Email:** admin@ecom.com
- **Password:** admin123

### Brands
Nike, Puma, Boat, Samsung, Levi's, Woodland, Fastrack, Noise

### Categories
Footwear, Electronics, Clothing, Accessories, Home & Kitchen, Sports

---

## Local Development

```bash
# Clone
git clone https://github.com/sheik-md-ali/apna-store.git
cd apna-store

# Install dependencies
npm install

# Create server/.env (see Environment Variables section)

# Create client/.env
echo "API_URL=http://localhost:3000/api" > client/.env

# Seed database
cd server && node utils/seed.js admin@ecom.com admin123 && cd ..

# Run both frontend and backend
npm run dev

# Frontend: http://localhost:8080
# Backend:  http://localhost:3000
```

---

## GitHub Repository

**URL:** https://github.com/sheik-md-ali/apna-store

**License:** MIT
