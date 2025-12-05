import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, g, flash, send_file
from io import BytesIO
import pdfkit
import os
import ast
import hashlib

app = Flask(__name__)
app.secret_key = "supersecretkey123"

app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# -----------------------------------------------------
# DATABASE FUNCTIONS
# -----------------------------------------------------
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect("database.db")
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def modify_db(query, args=()):
    db = get_db()
    db.execute(query, args)
    db.commit()

# -----------------------------------------------------
# HOME PAGE
# -----------------------------------------------------
@app.route("/")
def index():
    search = request.args.get("search", "")
    category = request.args.get("category", "")

    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if search:
        query += " AND name LIKE ?"
        params.append(f"%{search}%")
    if category:
        query += " AND category = ?"
        params.append(category)

    products = query_db(query, params)
    categories = query_db("SELECT DISTINCT category FROM products")

    nickname = None
    if "user" in session:
        user = query_db("SELECT nickname FROM users WHERE username = ?", [session["user"]], one=True)
        if user:
            nickname = user["nickname"]

    return render_template(
        "index.html",
        products=products,
        categories=categories,
        search_query=search,
        selected_category=category,
        nickname=nickname
    )

# -----------------------------------------------------
# PRODUCT PAGE
# -----------------------------------------------------
@app.route("/product/<int:product_id>")
def product_page(product_id):
    product = query_db("SELECT * FROM products WHERE id = ?", [product_id], one=True)
    variations = query_db("SELECT * FROM products WHERE category = ?", [product["category"]])
    return render_template("product.html", product=product, variations=variations)

# -----------------------------------------------------
# CART SYSTEM (VARIANT NAMES FIXED!)
# -----------------------------------------------------
@app.route("/add_to_cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    cart = session.get("cart", {})

    selected_image = request.form.get("selected_image")
    selected_name = request.form.get("selected_name", "")

    product = query_db("SELECT * FROM products WHERE id = ?", [product_id], one=True)
    product_image = selected_image if selected_image else product["image"]
    product_name = selected_name if selected_name else product["name"]

    pid_key = f"{product_id}_{product_image}"

    if pid_key in cart:
        cart[pid_key]["qty"] += 1
    else:
        cart[pid_key] = {
            "qty": 1,
            "image": product_image,
            "name": product_name,
            "price": product["price"]
        }

    session["cart"] = cart
    flash(f"✅ {product_name} added to cart!", "success")
    return redirect(url_for("cart"))

@app.route("/cart/increase/<cart_key>")
def increase_quantity(cart_key):
    cart = session.get("cart", {})
    if cart_key in cart:
        cart[cart_key]["qty"] += 1
    session["cart"] = cart
    return redirect(url_for("cart"))

@app.route("/cart/decrease/<cart_key>")
def decrease_quantity(cart_key):
    cart = session.get("cart", {})
    if cart_key in cart:
        if cart[cart_key]["qty"] > 1:
            cart[cart_key]["qty"] -= 1
        else:
            del cart[cart_key]
    session["cart"] = cart
    return redirect(url_for("cart"))

@app.route("/cart/remove/<cart_key>")
def remove_item(cart_key):
    cart = session.get("cart", {})
    if cart_key in cart:
        del cart[cart_key]
    session["cart"] = cart
    return redirect(url_for("cart"))

@app.route("/cart/clear")
def clear_cart():
    session["cart"] = {}
    flash("🛒 Cart cleared successfully!", "success")
    return redirect(url_for("cart"))

@app.route("/cart")
def cart():
    cart = session.get("cart", {})
    items = []
    total = 0

    for cart_key, data in cart.items():
        qty = data["qty"]
        image = data.get("image")
        name = data.get("name")
        price = data.get("price")

        subtotal = price * qty
        total += subtotal

        items.append({
            "cart_key": cart_key,
            "id": int(cart_key.split("_")[0]),
            "name": name,
            "qty": qty,
            "price": price,
            "image": image,
            "subtotal": subtotal
        })

    return render_template("cart.html", items=items, total=total)

# -----------------------------------------------------
# USER AUTHENTICATION (SIMPLE & FIXED!)
# -----------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        nickname = request.form['nickname'].strip()
        password = request.form['password'].strip()

        if not username or not nickname or not password:
            flash("❌ Please fill username, nickname, and password!", "danger")
            return render_template('register.html')

        # FIXED: Check username only (no email confusion)
        existing = query_db("SELECT id FROM users WHERE username = ?", [username], one=True)
        if existing:
            flash("❌ Username already exists! Choose another.", "danger")
            return render_template('register.html')

        # FIXED: Simple 3-column table (username, nickname, password)
        modify_db(
            "INSERT INTO users (username, nickname, password) VALUES (?, ?, ?)",
            [username, nickname, password]
        )

        flash('✅ Registered successfully! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        if not username or not password:
            flash("❌ Enter username and password!", "danger")
            return render_template("login.html")

        user = query_db(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            [username, password], one=True
        )

        if user:
            session["user"] = username
            flash("🎉 Welcome back, " + user['nickname'] + "!", "success")
            return redirect(url_for("index"))
        else:
            flash("❌ Wrong username or password!", "danger")
            return render_template("login.html")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("👋 Logged out successfully! See you soon.", "info")
    return redirect(url_for("index"))

# -----------------------------------------------------
# CHECKOUT + PDF RECEIPT
# -----------------------------------------------------
@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if "user" not in session:
        return redirect(url_for("login"))

    cart_items = session.get("cart", {})
    if not cart_items:
        flash("Your cart is empty!", "warning")
        return redirect(url_for("cart"))

    username = session["user"]

    if request.method == "POST":
        for cart_key, data in cart_items.items():
            qty = data["qty"]
            product_id = int(cart_key.split("_")[0])
            modify_db(
                "INSERT INTO orders (username, product_id, quantity) VALUES (?, ?, ?)",
                [username, product_id, qty]
            )

        orders = []
        total = 0
        user_info = query_db("SELECT nickname FROM users WHERE username = ?", [username], one=True)
        nickname = user_info["nickname"] if user_info else username

        for cart_key, data in cart_items.items():
            qty = data["qty"]
            img = data.get("image")
            name = data.get("name")
            price = data.get("price")
            subtotal = price * qty
            total += subtotal
            orders.append({
                "name": name,
                "qty": qty,
                "price": price,
                "subtotal": subtotal,
                "image": img
            })

        session["cart"] = {}
        flash("Order placed successfully!", "success")
        return render_template("receipt.html", orders=orders, total=total,
                               nickname=nickname, username=username)

    return render_template("checkout.html")

# -----------------------------------------------------
# DOWNLOAD RECEIPT
# -----------------------------------------------------
@app.route("/download_receipt", methods=["POST"])
def download_receipt():
    orders = ast.literal_eval(request.form.get("orders"))
    total = float(request.form.get("total"))
    nickname = request.form.get("nickname")
    username = request.form.get("username")

    options = {
        'enable-local-file-access': None,
        'allow': [os.path.join(app.root_path, 'static').replace('\\', '/')],
        'encoding': "UTF-8",
        'page-size': 'A4',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        'no-outline': None
    }

    static_base = url_for('static', filename='', _external=True)

    for item in orders:
        if item.get("image"):
            item["image_url"] = f"file:///{static_base}images/{item['image']}"
        else:
            item["image_url"] = ""

    wk_path = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    config = pdfkit.configuration(wkhtmltopdf=wk_path)

    html = render_template(
        "receipt_pdf.html",
        orders=orders,
        total=total,
        nickname=nickname,
        username=username,
        static_base=static_base
    )

    pdf_bytes = pdfkit.from_string(
        html,
        False,
        configuration=config,
        options=options
    )

    return send_file(
        BytesIO(pdf_bytes),
        download_name="receipt.pdf",
        as_attachment=True,
        mimetype="application/pdf"
    )

# -----------------------------------------------------
# ORDERS PAGE
# -----------------------------------------------------
@app.route("/orders")
def orders():
    if "user" not in session:
        return redirect(url_for("login"))

    username = session["user"]
    orders = query_db("""
        SELECT orders.id as order_id, orders.quantity, products.name, products.price, products.image
        FROM orders
        JOIN products ON orders.product_id = products.id
        WHERE orders.username = ?
        ORDER BY orders.id DESC
    """, [username])

    return render_template("orders.html", orders=orders)

@app.route("/orders/delete/<int:order_id>")
def delete_order(order_id):
    if "user" not in session:
        return redirect(url_for("login"))

    username = session["user"]
    modify_db("DELETE FROM orders WHERE id = ? AND username = ?", [order_id, username])
    flash("🗑️ Order removed successfully!", "success")
    return redirect(url_for("orders"))

if __name__ == "__main__":
    app.run(debug=True)
