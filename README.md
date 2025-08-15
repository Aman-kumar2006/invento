
# Invento — Cloud Inventory Manager

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3-lightgrey?logo=flask)](https://flask.palletsprojects.com/)
[![Supabase](https://img.shields.io/badge/Database-Supabase-brightgreen?logo=supabase)](https://supabase.com/)
[![Gunicorn](https://img.shields.io/badge/Server-Gunicorn-green?logo=gunicorn)](https://gunicorn.org/)
[![Render](https://img.shields.io/badge/Deploy-Render-blue?logo=render)](https://render.com/)

##  Overview
**Invento** is a cloud-based inventory and sales tracking system built with **Flask** and **Supabase**.  
It replaces local SQLite storage with Supabase’s hosted PostgreSQL so your data is accessible anywhere.  
Features include:
- Add, update, delete products
- Track inventory in real-time
- Record and view sales
- Generate monthly sales reports with charts
- Cloud-hosted database (Supabase)

---

##  Database Schema

### **Table: `products`**
| Column     | Type      | Description                   |
|------------|-----------|-------------------------------|
| id         | int (PK)  | Auto-generated product ID      |
| name       | text      | Product name                   |
| price      | numeric   | Product price (₹)              |
| quantity   | int       | Quantity in stock              |

### **Table: `sales`**
| Column     | Type      | Description                   |
|------------|-----------|-------------------------------|
| id         | int (PK)  | Auto-generated sale ID         |
| product_id | int (FK)  | References `products.id`       |
| quantity   | int       | Quantity sold                  |
| total_price| numeric   | Total sale amount              |
| date       | date      | Date of sale                   |

---

## ⚙️ Environment Variables

Create a `.env` file in your project root:

```env
SUPABASE_URL=https://<your-project-id>.supabase.co
SUPABASE_KEY=<your-service-role-or-anon-key>
FLASK_SECRET=some_long_secret
````

>  **Never commit `.env` to GitHub!**

---

##  Local Development

### **1. Clone the repository**

```bash
git clone https://github.com/<your-username>/invento.git
cd invento
```

### **2. Create a virtual environment if you need**

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### **3. Install dependencies**

```bash
pip install -r requirements.txt
```

### **4. Run the app**

```bash
flask run
```

---

## 🚀 Deployment (Render.com)

1. Push your project to GitHub.
2. Go to [Render](https://render.com) → **New Web Service**.
3. Connect your GitHub repo.
4. Add your `.env` variables in Render's **Environment** tab.
5. Set **Build Command**:

   ```bash
   pip install -r requirements.txt
   ```
6. Set **Start Command**:

   ```bash
   gunicorn invento:app
   ```
7. Deploy!

---



##  License

MIT License — feel free to use, modify, and share.

---

> Built with ❤ using **Flask** + **Supabase** for a modern, cloud-first inventory system.





I can also make you a **`requirements.txt`** and **`Procfile`** so this README lines up with your deployment workflow.  
Do you want me to prepare those next so your GitHub repo is 100% deploy-ready?
```
