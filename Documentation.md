# Backend Only Docs

---

# 🛠️ **AoATraders An e-commerce plateform**

## **_Backend-Only Technical Architecture & Feature Documentation_**

### 🔭 **Project Vision**

We're building a **smart, scalable B2B/B2C platform** that connects companies needing safety equipment with multiple suppliers. Here's what we're aiming for:

- Handle millions of products per supplier
- Auto-check uploaded certifications for compliance
- Merge product catalogs from different companies into one searchable marketplace
- Keep everything secure and easy to maintain

---

## 💻 **Tech Stack (Backend)**

- **FastAPI**  
  → For building all backend APIs

- **Pandas**  
  → For cleaning, transforming, and reading file uploads

- **Sentence-transformers**  
  → For understanding context between column names using embeddings

- **Scikit-learn**  
  → For model-driven matching, anomaly detection, etc.

- **Pydantic**  
  → For strict data validation and serialization
- **PostgreSql/MYSQL**  
  → For saving data (it shoule be only mysql or postgres but postres is recommended)

---

## 🧠 **AI-Powered Column Mapping for File Uploads**

### 🧾 Problem We're Solving:

When different companies upload product data, their column names don't always match what our database expects. For example:

- Supplier uploads:  
  `about-product`, `cost`, `manufacturer-name`

- Our DB expects:  
  `description_product`, `price`, `vendor_name`

---

### 🧠 How AI Helps

When a **supplier uploads a CSV or Excel file**, here's what happens:

1. **Upload**:  
   A user from a supplier company uploads their product file through our system.

2. **Schema Inference with AI**:  
   Behind the scenes, we use **sentence-transformers** to **compare the column names** from their file to our database schema.  
   This comparison is based on the **meaning of the words**, not the exact spelling.

3. **Auto-Mapping Suggestions**:  
   The AI model figures out that `about-product` likely means the same as `description_project`. It then suggests this mapping and applies it automatically.

4. **User Feedback (Optional)**:  
   We can optionally show the user a preview:

   > “We’ve detected `about-product` likely maps to `description_project`. Want to confirm?”

5. **Processed & Stored**:  
   Once mapped, the file is cleaned and inserted into the database in the correct format.

---

### 🧪 Tech Stack Behind the Scenes

- **Sentence-transformers** (e.g. `all-MiniLM-L6-v2`) → Used to create vector embeddings of column names.
- **Cosine similarity** → Measures how closely the uploaded columns match our known schema.
- **Pandas** → Used to parse, transform, and remap the uploaded files.
- **Fallback Option** → If confidence score is low, we flag it for manual mapping.

---

## 🧰 **Key Backend Features Explained**

---

### 🔐 1. Authentication

When a new user signs up or logs in:

- **Social Login**
  - User can signup and signin through social accounts like google and facebook
- **Email login**
  - Depending on their role (Admin, Supplier, Buyer), they get access to different parts of the system
  - Everything is permission-controlled—users can only do what they’re allowed to do
  - Verify user through Magic link of 1 time click (otp not recommended)

## Note: Also take username which will be unique even user is signing up from social accounts

---

---

### 📦 2. Product Uploads (Bulk)

A supplier logs in, goes to the dashboard, and uploads a file with their product data.

- We read it in chunks to handle large files
- If the user have completely wrong data then we can throw error otherwise we are responsible to fix that error through AI
- You will send the message to the supplier about the fields you are manipulating
- We automatically clean and transform the data using AI (as explained above)
- We insert it into the product table if all checks pass

---

### 📊 3. Dashboard

Once logged in:

- **Suppliers** see: Number of products uploaded, success/error logs, latest certifications
- **Admins** see: Total users, flagged uploads, top-selling products, etc.
- Stats can be exported as CSV/Excel

---

### 🛒 4. Cart & Wishlist

Buyers can:

- Add products to their cart (multi-supplier supported)
- Save products they like to their wishlist
- Proceed to checkout from their cart

Cart gets auto-cleared after a successful order.

---

### 🧾 5. Order Management

Buyers/Customers:

- Place orders
- Get live status updates (pending, shipped, delivered)
- Basically customer is same as any typical customer in e-commerce site

Suppliers:

- Accept or reject orders
- Track inventory changes
- Get notified of low stock

Admins & Moderator:

- Can Control whole website from dashboard. Can delete and modify anyone. Can see the history of uploads orders
- Monitor all orders platform-wide
- Moderator can do all the stuff admin can do but he have to get the approval like if moderatory want to delete something from the website in his prespective it is deleted but for admin it is soft-deleted. It is just as `Trash` folder in any desktop operating system

---

### 💬 6. Reviews & Ratings

After an order is delivered:

- Buyers can leave a star rating and optional comment
- Only verified purchases are allowed to post reviews
- Suppliers can respond to reviews

This builds transparency and trust in the marketplace.

---

### 💳 7. Checkout + Payments

From the cart, the buyer clicks “Checkout”:

- We break the cart into multiple supplier orders if needed
- Payment happens through Stripe (will be shared later)
- We confirm each transaction and notify all parties

If something goes wrong, we roll it back and notify the user.

---

### 🧾 8. Compliance Engine

After uploading products, a supplier can also upload certification files (PDF or scans).

- We extract the document content (OCR for scans)
- We check it against expected compliance rules (e.g. ISO formats, expiry dates)
- If something’s missing or expired, we flag it for the supplier to fix

## 🎯 Milestones & Goals

| **Phase** | **Goal**                              |
| --------- | ------------------------------------- |
| Week 1–2  | Auth, File Upload, AI mapping working |
| Week 3–4  | Orders, Cart, Reviews, Compliance     |
| Week 5+   | Dashboard, Security, Stress testing   |

---

### **Security**

- Protect site from commone attacks like DDOS, CSRF, SQL injection
- Use Ratelimiter to proect the endpoint from spamming like user can logout and login only for 5 time under 5 minutes

## 👨‍💻 **Backend Developer Responsibilities**

- Write highly maintainable, modular code
- No file exceeds **150 lines**
- Follow **OOP** principles
- Fully **type-safe** code using Pydantic & type hints
- Ensure **robust error handling**
- Optimize DB queries to **minimize unnecessary calls**
- Maintain:
  - Code **quality**
  - High **readability**
  - System **performance**
  - **Decoupling** across all modules

---

---

## 📁 **Project Folder Structure For inspiration**

```plaintext
app/
├── main.py
├── config/
│   └── settings.py
├── api/
│   ├── routes/
│   │   ├── auth.py
│   │   ├── product.py
│   │   ├── cart.py
│   │   ├── order.py
│   │   └── admin.py
│   └── version1/
│       └── route_init.py
├── core/
│   ├── app.py
│   ├── security.py
│   └── middleware.py
├── models/
│   ├── user.py
│   ├── product.py
│   ├── order.py
│   ├── review.py
│   └── wishlist.py
├── schemas/
│   ├── auth.py
│   ├── product.py
│   ├── order.py
│   └── review.py
├── crud/
│   ├── user.py
│   ├── product.py
│   ├── order.py
│   └── review.py
├── services/
│   ├── product_service.py
│   ├── auth_service.py
│   └── order_service.py
├── utils/
│   ├── hashing.py
│   └── embedding.py
tests/
├── test_auth.py
├── test_product.py
└── test_order.py
```

---

---

### 💡 Note

> Even if you are full stack developer you are responsible for writing `Documentation` for frontend developoer with proper responses also you must make sure frontend developer is aware of all the edge cases through api documentation. Use any open-source tool to write `api` Documentation

---
