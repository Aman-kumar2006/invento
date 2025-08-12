# # app.py
# import os
# import io
# from datetime import datetime
# from dotenv import load_dotenv

# from flask import Flask, render_template, request, redirect, url_for, flash, Response
# from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
# from werkzeug.security import generate_password_hash, check_password_hash

# from supabase import create_client, Client
# import pandas as pd
# import matplotlib
# matplotlib.use('Agg')
# import matplotlib.pyplot as plt
# from reportlab.lib.pagesizes import letter
# from reportlab.pdfgen import canvas

# # --------- Load config ----------
# load_dotenv()

# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_KEY")
# FLASK_SECRET = os.getenv("FLASK_SECRET", "please-change-me")

# if not SUPABASE_URL or not SUPABASE_KEY:
#     raise RuntimeError("Set SUPABASE_URL and SUPABASE_KEY in your environment (.env)")

# supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# # --------- Flask setup ----------
# app = Flask(__name__)
# app.secret_key = FLASK_SECRET

# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = "login"


# # --------- User model ---------
# class User(UserMixin):
#     def __init__(self, id_, username, pw_hash):
#         self.id = str(id_)   # flask-login expects a string id
#         self.username = username
#         self.pw_hash = pw_hash


# @login_manager.user_loader
# def load_user(user_id):
#     try:
#         # user_id is stored as a string by flask-login; convert to int for query
#         q = supabase.table("users").select("*").eq("id", int(user_id)).single().execute()
#         data = q.data
#         if data and isinstance(data, dict):
#             return User(data["id"], data["username"], data["password"])
#     except Exception:
#         pass
#     return None


# # --------- Helper: ensure admin exists (best-effort) ----------
# def ensure_admin():
#     try:
#         q = supabase.table("users").select("*").eq("username", "admin").limit(1).execute()
#         if not q.data:
#             hashed = generate_password_hash("admin123")
#             supabase.table("users").insert({"username": "admin", "password": hashed}).execute()
#     except Exception:
#         # If table doesn't exist or permission denied, ignore here.
#         pass


# ensure_admin()


# # --------- Routes ----------
# @app.route("/")
# @login_required
# def index():
#     try:
#         resp = supabase.table("inventory").select("*").order("id", {"ascending": True}).execute()
#         items = resp.data or []
#     except Exception:
#         items = []
#     return render_template("index.html", items=items)


# @app.route("/register", methods=["GET", "POST"])
# def register():
#     # Lightweight register route (no email verification) for quick onboarding
#     if request.method == "POST":
#         username = request.form.get("username", "").strip()
#         password = request.form.get("password", "")
#         if not username or not password:
#             flash("Username and password required.", "danger")
#             return redirect(url_for("register"))
#         # check exists
#         q = supabase.table("users").select("id").eq("username", username).limit(1).execute()
#         if q.data:
#             flash("Username already exists.", "warning")
#             return redirect(url_for("register"))
#         hashed = generate_password_hash(password)
#         supabase.table("users").insert({"username": username, "password": hashed}).execute()
#         flash("Account created. Please log in.", "success")
#         return redirect(url_for("login"))
#     return render_template("register.html")


# @app.route("/login", methods=["GET", "POST"])
# def login():
#     if request.method == "POST":
#         username = request.form.get("username", "").strip()
#         password = request.form.get("password", "")
#         if not username or not password:
#             flash("Provide both username and password.", "danger")
#             return redirect(url_for("login"))
#         q = supabase.table("users").select("*").eq("username", username).single().execute()
#         data = q.data
#         if data and check_password_hash(data.get("password", ""), password):
#             user_obj = User(data["id"], data["username"], data["password"])
#             login_user(user_obj)
#             flash("Logged in successfully!", "success")
#             return redirect(url_for("index"))
#         flash("Invalid credentials. Try again.", "danger")
#     return render_template("login.html")


# @app.route("/logout")
# @login_required
# def logout():
#     logout_user()
#     flash("Logged out.", "success")
#     return redirect(url_for("login"))


# @app.route("/add", methods=["GET", "POST"])
# @login_required
# def add_item():
#     if request.method == "POST":
#         try:
#             data = {
#                 "name": request.form.get("name", "").strip(),
#                 "quantity": int(request.form.get("quantity") or 0),
#                 "price": float(request.form.get("price") or 0.0),
#                 "supplier": request.form.get("supplier", "").strip(),
#                 "category": request.form.get("category", "").strip(),
#                 "barcode": request.form.get("barcode", "").strip(),
#             }
#             supabase.table("inventory").insert(data).execute()
#             flash("Item added!", "success")
#         except Exception as e:
#             flash(f"Failed to add item: {e}", "danger")
#         return redirect(url_for("index"))
#     return render_template("add_item.html", item=None)


# @app.route("/update/<int:item_id>", methods=["GET", "POST"])
# @login_required
# def update_item(item_id):
#     if request.method == "POST":
#         try:
#             data = {
#                 "name": request.form.get("name", "").strip(),
#                 "quantity": int(request.form.get("quantity") or 0),
#                 "price": float(request.form.get("price") or 0.0),
#                 "supplier": request.form.get("supplier", "").strip(),
#                 "category": request.form.get("category", "").strip(),
#                 "barcode": request.form.get("barcode", "").strip(),
#             }
#             supabase.table("inventory").update(data).eq("id", item_id).execute()
#             flash("Item updated!", "success")
#             return redirect(url_for("index"))
#         except Exception as e:
#             flash(f"Update failed: {e}", "danger")
#             return redirect(url_for("index"))

#     q = supabase.table("inventory").select("*").eq("id", item_id).single().execute()
#     item = q.data if q.data else None
#     return render_template("add_item.html", item=item)


# @app.route("/delete/<int:item_id>", methods=["POST"])
# @login_required
# def delete_item(item_id):
#     try:
#         supabase.table("inventory").delete().eq("id", item_id).execute()
#         flash("Item deleted!", "success")
#     except Exception as e:
#         flash(f"Delete failed: {e}", "danger")
#     return redirect(url_for("index"))


# @app.route("/sell/<int:item_id>", methods=["GET", "POST"])
# @login_required
# def sell_item(item_id):
#     q = supabase.table("inventory").select("*").eq("id", item_id).single().execute()
#     item = q.data if q.data else None
#     if not item:
#         flash("Item not found.", "danger")
#         return redirect(url_for("index"))

#     if request.method == "POST":
#         try:
#             qty = int(request.form.get("quantity") or 0)
#             buyer = request.form.get("buyer", "").strip()
#             if qty <= 0:
#                 flash("Quantity must be > 0", "warning")
#                 return render_template("sell_item.html", item=item)
#             if qty > (item.get("quantity") or 0):
#                 flash("Not enough stock.", "danger")
#                 return render_template("sell_item.html", item=item)

#             new_qty = (item.get("quantity") or 0) - qty
#             total_price = qty * (item.get("price") or 0.0)
#             today = datetime.now().strftime("%Y-%m-%d")

#             # update inventory
#             supabase.table("inventory").update({"quantity": new_qty}).eq("id", item_id).execute()

#             # insert sale
#             res = supabase.table("sales").insert({
#                 "product_id": item_id,
#                 "product_name": item.get("name"),
#                 "quantity": qty,
#                 "total_price": total_price,
#                 "date": today,
#                 "buyer": buyer
#             }).execute()

#             # supabase returns list of inserted rows under .data
#             sale_id = None
#             if res.data:
#                 # sometimes it's a list; sometimes a dict — handle both
#                 if isinstance(res.data, list) and len(res.data) > 0:
#                     sale_id = res.data[0].get("id")
#                 elif isinstance(res.data, dict):
#                     sale_id = res.data.get("id")

#             flash(f'Sale recorded! <a href="{ url_for("download_invoice", sale_id=sale_id) }" class="alert-link">Download Invoice</a>', "success")
#             return redirect(url_for("index"))
#         except Exception as e:
#             flash(f"Failed to record sale: {e}", "danger")
#             return render_template("sell_item.html", item=item)

#     return render_template("sell_item.html", item=item)


# @app.route("/invoice/<int:sale_id>")
# @login_required
# def download_invoice(sale_id):
#     q = supabase.table("sales").select("*").eq("id", sale_id).single().execute()
#     sale = q.data if q.data else None
#     if not sale:
#         flash("Invoice not found.", "danger")
#         return redirect(url_for("index"))

#     buffer = io.BytesIO()
#     c = canvas.Canvas(buffer, pagesize=letter)
#     c.setFont("Helvetica-Bold", 22)
#     c.drawString(220, 770, "INVOICE")
#     c.setFont("Helvetica", 12)
#     c.drawString(50, 730, f"Invoice #: {sale.get('id')}")
#     c.drawString(50, 710, f"Date: {sale.get('date')}")
#     c.drawString(50, 690, f"Buyer: {sale.get('buyer')}")
#     c.line(50, 685, 550, 685)
#     c.drawString(50, 670, f"Item: {sale.get('product_name')}")
#     c.drawString(50, 650, f"Quantity: {sale.get('quantity')}")
#     c.drawString(50, 630, f"Total: ₹{float(sale.get('total_price') or 0):.2f}")
#     c.drawString(50, 610, "Thank you for your purchase!")
#     c.save()
#     buffer.seek(0)
#     return Response(buffer, mimetype="application/pdf", headers={"Content-Disposition": f"attachment;filename=invoice_{sale.get('id')}.pdf"})


# @app.route("/export_inventory")
# @login_required
# def export_inventory():
#     q = supabase.table("inventory").select("*").order("id", {"ascending": True}).execute()
#     df = pd.DataFrame(q.data or [])
#     buf = io.StringIO()
#     df.to_csv(buf, index=False)
#     buf.seek(0)
#     return Response(buf.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=inventory_export.csv"})


# @app.route("/export_sales")
# @login_required
# def export_sales():
#     q = supabase.table("sales").select("*").order("id", {"ascending": True}).execute()
#     df = pd.DataFrame(q.data or [])
#     buf = io.StringIO()
#     df.to_csv(buf, index=False)
#     buf.seek(0)
#     return Response(buf.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=sales_export.csv"})


# @app.route("/report")
# @login_required
# def report():
#     # Fetch all sales and aggregate by date in Python (safe and simple)
#     q = supabase.table("sales").select("*").order("date", {"ascending": True}).execute()
#     sales = q.data or []

#     if not sales:
#         flash("No sales data!", "info")
#         return render_template("report.html", sales=None, chart_img=None)

#     # Aggregate by date
#     df = pd.DataFrame(sales)
#     # ensure date column exists
#     if "date" not in df.columns:
#         flash("Sales have no date info.", "warning")
#         return render_template("report.html", sales=None, chart_img=None)

#     agg = df.groupby("date").agg(total_qty=("quantity", "sum"), total_rev=("total_price", "sum")).reset_index()
#     dates = agg["date"].tolist()
#     quantities = agg["total_qty"].tolist()
#     revenues = agg["total_rev"].tolist()

#     plt.style.use("dark_background")
#     fig, ax1 = plt.subplots(figsize=(8, 4))
#     ax1.bar(dates, quantities, label="Items Sold")
#     ax2 = ax1.twinx()
#     ax2.plot(dates, revenues, marker="o", label="Total Revenue")
#     ax1.set_xlabel("Date")
#     ax1.set_ylabel("Items Sold")
#     ax2.set_ylabel("Revenue (₹)")
#     ax1.tick_params(axis="x", rotation=45)
#     fig.tight_layout()

#     chart_buf = io.BytesIO()
#     plt.savefig(chart_buf, format="png", bbox_inches="tight")
#     plt.close(fig)
#     chart_buf.seek(0)

#     # We can serve the chart as a data URL in template or save to static — we'll provide raw bytes to template via encoding
#     import base64
#     chart_b64 = base64.b64encode(chart_buf.getvalue()).decode("utf-8")
#     chart_data = f"data:image/png;base64,{chart_b64}"

#     # send aggregated sales records and chart_data to template
#     sales_list = agg.to_dict(orient="records")
#     return render_template("report.html", sales=sales_list, chart_img=chart_data)


# # --------- Run ----------
# if __name__ == "__main__":
#     # debug True for development only
#     app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))


from flask import Flask, render_template, request, redirect, url_for, flash, send_file, Response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import os
from datetime import datetime

# Load env vars
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
FLASK_SECRET = os.getenv("FLASK_SECRET", "secret")

# Init Flask
app = Flask(__name__)
app.secret_key = FLASK_SECRET

# Init Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Init Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id_, username, pw_hash):
        self.id = id_
        self.username = username
        self.pw_hash = pw_hash

# Ensure default admin exists
existing_admin = supabase.table("users").select("*").eq("username", "admin").execute()
if not existing_admin.data:
    supabase.table("users").insert({
        "username": "admin",
        "password": generate_password_hash("admin123")
    }).execute()

@login_manager.user_loader
def load_user(user_id):
    user = supabase.table("users").select("*").eq("id", user_id).execute()
    if user.data:
        u = user.data[0]
        return User(u["id"], u["username"], u["password"])
    return None

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    items = supabase.table("inventory").select("*").execute().data
    return render_template("index.html", items=items)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        res = supabase.table("users").select("*").eq("username", username).execute()
        if res.data and check_password_hash(res.data[0]["password"], password):
            user_obj = User(res.data[0]["id"], res.data[0]["username"], res.data[0]["password"])
            login_user(user_obj)
            flash("Logged in successfully!", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials. Try again.", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "success")
    return redirect(url_for("login"))

@app.route("/add", methods=["GET", "POST"])
@login_required
def add_item():
    if request.method == "POST":
        data = {
            "name": request.form["name"],
            "quantity": int(request.form["quantity"]),
            "price": float(request.form["price"]),
            "supplier": request.form["supplier"],
            "category": request.form["category"],
            "barcode": request.form["barcode"]
        }
        supabase.table("inventory").insert(data).execute()
        flash("Item added!", "success")
        return redirect(url_for("index"))
    return render_template("add_item.html", item=None)

@app.route("/update/<int:item_id>", methods=["GET", "POST"])
@login_required
def update_item(item_id):
    item = supabase.table("inventory").select("*").eq("id", item_id).execute().data[0]
    if request.method == "POST":
        updated_data = {
            "name": request.form["name"],
            "quantity": int(request.form["quantity"]),
            "price": float(request.form["price"]),
            "supplier": request.form["supplier"],
            "category": request.form["category"],
            "barcode": request.form["barcode"]
        }
        supabase.table("inventory").update(updated_data).eq("id", item_id).execute()
        flash("Item updated!", "success")
        return redirect(url_for("index"))
    return render_template("add_item.html", item=item)

@app.route("/delete/<int:item_id>", methods=["POST"])
@login_required
def delete_item(item_id):
    supabase.table("inventory").delete().eq("id", item_id).execute()
    flash("Item deleted!", "success")
    return redirect(url_for("index"))

@app.route("/sell/<int:item_id>", methods=["GET", "POST"])
@login_required
def sell_item(item_id):
    item = supabase.table("inventory").select("*").eq("id", item_id).execute().data[0]
    if request.method == "POST":
        qty = int(request.form["quantity"])
        buyer = request.form["buyer"]
        if qty > item["quantity"]:
            flash("Not enough stock.", "danger")
            return render_template("sell_item.html", item=item)
        new_qty = item["quantity"] - qty
        total_price = qty * item["price"]
        today = datetime.now().strftime("%Y-%m-%d")
        supabase.table("inventory").update({"quantity": new_qty}).eq("id", item_id).execute()
        sale = supabase.table("sales").insert({
            "product_id": item_id,
            "product_name": item["name"],
            "quantity": qty,
            "total_price": total_price,
            "date": today,
            "buyer": buyer
        }).execute()
        sale_id = sale.data[0]["id"]
        flash(f'Sale recorded! <a href="{url_for("download_invoice", sale_id=sale_id)}" class="alert-link">Download Invoice</a>', "success")
        return redirect(url_for("index"))
    return render_template("sell_item.html", item=item)

@app.route("/invoice/<int:sale_id>")
@login_required
def download_invoice(sale_id):
    sale = supabase.table("sales").select("*").eq("id", sale_id).execute().data[0]
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(220, 770, "INVOICE")
    c.setFont("Helvetica", 12)
    c.drawString(50, 730, f"Invoice #: {sale['id']}")
    c.drawString(50, 710, f"Date: {sale['date']}")
    c.drawString(50, 690, f"Buyer: {sale['buyer']}")
    c.line(50, 685, 550, 685)
    c.drawString(50, 670, f"Item: {sale['product_name']}")
    c.drawString(50, 650, f"Quantity: {sale['quantity']}")
    c.drawString(50, 630, f"Total: ₹{sale['total_price']:.2f}")
    c.drawString(50, 610, "Thank you for your purchase!")
    c.save()
    buffer.seek(0)
    return Response(buffer, mimetype="application/pdf",
                    headers={"Content-Disposition": f"attachment;filename=invoice_{sale['id']}.pdf"})

@app.route("/export_inventory")
@login_required
def export_inventory():
    items = supabase.table("inventory").select("*").execute().data
    df = pd.DataFrame(items)
    filename = "inventory_export.csv"
    df.to_csv(filename, index=False)
    return send_file(filename, as_attachment=True)

@app.route("/export_sales")
@login_required
def export_sales():
    sales = supabase.table("sales").select("*").execute().data
    df = pd.DataFrame(sales)
    filename = "sales_export.csv"
    df.to_csv(filename, index=False)
    return send_file(filename, as_attachment=True)

@app.route("/report")
@login_required
def report():
    sales = supabase.rpc("get_sales_summary").execute().data
    if sales:
        dates = [s["date"] for s in sales]
        quantities = [s["total_qty"] for s in sales]
        revenues = [s["total_rev"] for s in sales]
        plt.style.use("dark_background")
        fig, ax1 = plt.subplots(figsize=(8, 4))
        ax1.bar(dates, quantities, color="cyan", label="Items Sold")
        ax2 = ax1.twinx()
        ax2.plot(dates, revenues, color="orange", marker="o", label="Total Revenue")
        ax1.set_xlabel("Date")
        ax1.set_ylabel("Items Sold", color="cyan")
        ax2.set_ylabel("Revenue (₹)", color="orange")
        ax1.tick_params(axis="x", rotation=45)
        fig.tight_layout()
        chart_path = os.path.join("static", "report.png")
        plt.savefig(chart_path)
        plt.close()
        return render_template("report.html", sales=sales, chart_img="report.png")
    else:
        flash("No sales data!", "info")
        return render_template("report.html", sales=None, chart_img=None)

if __name__ == "__main__":
    app.run(debug=True)
