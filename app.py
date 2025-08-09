from flask import Flask, render_template, request, redirect, url_for, flash, send_file, Response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id_, username, pw_hash):
        self.id = id_
        self.username = username
        self.pw_hash = pw_hash

def get_db():
    conn = sqlite3.connect('inventory.db')
    conn.row_factory = sqlite3.Row
    return conn

# ----- Initial DB Setup -----
with get_db() as conn:
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, quantity INTEGER, price REAL,
        supplier TEXT, category TEXT, barcode TEXT
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        product_name TEXT,
        quantity INTEGER,
        total_price REAL,
        date TEXT,
        buyer TEXT
    )''')
    # Add default admin if not exists
    user = conn.execute('SELECT * FROM users WHERE username=?', ('admin',)).fetchone()
    if not user:
        conn.execute('INSERT INTO users (username, password) VALUES (?,?)', (
            'admin', generate_password_hash('admin123')
        ))

@login_manager.user_loader
def load_user(user_id):
    with get_db() as conn:
        user = conn.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
        if user:
            return User(user['id'], user['username'], user['password'])
    return None

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    with get_db() as conn:
        items = conn.execute('SELECT * FROM inventory').fetchall()
    return render_template('index.html', items=items)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with get_db() as conn:
            user = conn.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
        if user and check_password_hash(user['password'], password):
            user_obj = User(user['id'], user['username'], user['password'])
            login_user(user_obj)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials. Try again.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        name = request.form['name']
        quantity = request.form['quantity']
        price = request.form['price']
        supplier = request.form['supplier']
        category = request.form['category']
        barcode = request.form['barcode']
        with get_db() as conn:
            conn.execute('INSERT INTO inventory (name, quantity, price, supplier, category, barcode) VALUES (?, ?, ?, ?, ?, ?)',
                         (name, quantity, price, supplier, category, barcode))
        flash('Item added!', 'success')
        return redirect(url_for('index'))
    return render_template('add_item.html', item=None)

@app.route('/update/<int:item_id>', methods=['GET', 'POST'])
@login_required
def update_item(item_id):
    with get_db() as conn:
        item = conn.execute('SELECT * FROM inventory WHERE id=?', (item_id,)).fetchone()
        if request.method == 'POST':
            data = (
                request.form['name'], request.form['quantity'], request.form['price'],
                request.form['supplier'], request.form['category'], request.form['barcode'], item_id
            )
            conn.execute('UPDATE inventory SET name=?, quantity=?, price=?, supplier=?, category=?, barcode=? WHERE id=?', data)
            flash('Item updated!', 'success')
            return redirect(url_for('index'))
    return render_template('add_item.html', item=item)

@app.route('/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    with get_db() as conn:
        conn.execute('DELETE FROM inventory WHERE id=?', (item_id,))
    flash('Item deleted!', 'success')
    return redirect(url_for('index'))

@app.route('/sell/<int:item_id>', methods=['GET', 'POST'])
@login_required
def sell_item(item_id):
    with get_db() as conn:
        item = conn.execute('SELECT * FROM inventory WHERE id=?', (item_id,)).fetchone()
        if request.method == 'POST':
            qty = int(request.form['quantity'])
            buyer = request.form['buyer']
            if qty > item['quantity']:
                flash("Not enough stock.", 'danger')
                return render_template('sell_item.html', item=item)
            new_qty = item['quantity'] - qty
            total_price = qty * item['price']
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')
            conn.execute('UPDATE inventory SET quantity=? WHERE id=?', (new_qty, item_id))
            cur = conn.execute('INSERT INTO sales (product_id, product_name, quantity, total_price, date, buyer) VALUES (?, ?, ?, ?, ?, ?)',
                         (item_id, item['name'], qty, total_price, today, buyer))
            sale_id = cur.lastrowid
            flash(f'Sale recorded! <a href="{ url_for("download_invoice", sale_id=sale_id) }" class="alert-link">Download Invoice</a>', 'success')
            return redirect(url_for('index'))
    return render_template('sell_item.html', item=item)

@app.route('/invoice/<int:sale_id>')
@login_required
def download_invoice(sale_id):
    with get_db() as conn:
        sale = conn.execute('SELECT * FROM sales WHERE id=?', (sale_id,)).fetchone()
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
    return Response(buffer, mimetype='application/pdf',
                    headers={"Content-Disposition":f"attachment;filename=invoice_{sale['id']}.pdf"})

@app.route('/export_inventory')
@login_required
def export_inventory():
    with get_db() as conn:
        df = pd.read_sql('SELECT * FROM inventory', conn)
    filename = 'inventory_export.csv'
    df.to_csv(filename, index=False)
    return send_file(filename, as_attachment=True)

@app.route('/export_sales')
@login_required
def export_sales():
    with get_db() as conn:
        df = pd.read_sql('SELECT * FROM sales', conn)
    filename = 'sales_export.csv'
    df.to_csv(filename, index=False)
    return send_file(filename, as_attachment=True)

@app.route('/report')
@login_required
def report():
    with get_db() as conn:
        sales = conn.execute('SELECT date, SUM(quantity) as total_qty, SUM(total_price) as total_rev FROM sales GROUP BY date').fetchall()
    if sales:
        dates = [s['date'] for s in sales]
        quantities = [s['total_qty'] for s in sales]
        revenues = [s['total_rev'] for s in sales]

        plt.style.use('dark_background')
        fig, ax1 = plt.subplots(figsize=(8,4))
        ax1.bar(dates, quantities, color='cyan', label='Items Sold')
        ax2 = ax1.twinx()
        ax2.plot(dates, revenues, color='orange', marker='o', label='Total Revenue')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Items Sold', color='cyan')
        ax2.set_ylabel('Revenue (₹)', color='orange')
        ax1.tick_params(axis='x', rotation=45)
        fig.tight_layout()
        chart_path = os.path.join('static', 'report.png')
        plt.savefig(chart_path)
        plt.close()
        return render_template('report.html', sales=sales, chart_img='report.png')
    else:
        flash("No sales data!", 'info')
        return render_template('report.html', sales=None, chart_img=None)

if __name__ == "__main__":
    app.run(debug=True)
