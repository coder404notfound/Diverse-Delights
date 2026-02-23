from flask import Flask, render_template, request, redirect, session, url_for
from extensions import db
from models.product import Product
from models.category import Category
from models.user import User
from models.review import Review
from models.wishlist import Wishlist
from models.cart import Cart, CartItem
from models.order import Order
from models.order_item import OrderItem
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from functools import wraps
import random
import time
import re
import os
import razorpay
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart



# Flask App Initialization

app = Flask(__name__)



# Load environment variables

load_dotenv()
app.secret_key = os.getenv("SECRET_KEY")



# Database Configuration

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)



# Create tables if they don't exist

with app.app_context():
    db.create_all()



# Razorpay Client Initialization

client = razorpay.Client(
    auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))
)



# Email Utility

def send_email(to_email, subject, body):
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")
    sender_name = os.getenv("EMAIL_FROM", "Diverse Delights")

    # Basic check to ensure email credentials are set before attempting to send an email.

    if not sender_email or not sender_password:
        print("Email credentials not configured properly.")
        return

    # Construct the email message

    msg = MIMEMultipart()
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = to_email
    msg["Subject"] = subject

    # Attach the email body as plain text

    msg.attach(MIMEText(body, "plain"))

    # Send the email using SMTP server (Gmail in this case).

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"Email sent to {to_email}")
    except Exception as e:
        print("Email error:", e)



# Specific Emails

# OTP Email for Password Reset

def send_otp_email(to_email, otp):
    subject = "Your OTP Code - Diverse Delights"
    body = f"""
Hello,

Your OTP is: {otp}
This OTP will expire in 2 minutes.

If you did not request this, please ignore this email.

- Diverse Delights
"""
    send_email(to_email, subject, body)

# Welcome Email

def send_welcome_email(user):
    subject = "Welcome to Diverse Delights 🎉"
    body = f"""
Hi {user.first_name},

Welcome to Diverse Delights!

Your account has been successfully created.

We’re excited to have you onboard.

Happy shopping!

- Team Diverse Delights
"""
    send_email(user.email, subject, body)

# Password Changed Email

def send_password_changed_email(user):
    subject = "Password Updated - Diverse Delights"
    body = f"""
Hi {user.first_name},

Your password has been successfully updated.

If this wasn't you, please contact support immediately.

- Diverse Delights
"""
    send_email(user.email, subject, body)

# Order Confirmation Email

def send_order_confirmation_email(user, order):
    subject = f"Order #{order.id} Confirmation - Diverse Delights"
    body = f"""
Hi {user.first_name},

Thank you for your order!

Order ID: {order.id}
Total Amount: ₹{order.total_amount}
Payment Method: {order.payment_method}
Order Status: {order.order_status}

We will notify you when your order status changes.

- Diverse Delights
"""
    send_email(user.email, subject, body)

# Order Status Update Email

def send_order_status_update_email(order):
    subject = f"Order #{order.id} Status Update"
    body = f"""
Hello {order.user.first_name},

Your order #{order.id} is now:
{order.order_status}

Thank you for shopping with us!

- Diverse Delights
"""
    send_email(order.user.email, subject, body)

# Payment Status Update Email

def send_payment_status_update_email(order):
    subject = f"Payment Update for Order #{order.id}"
    body = f"""
Hello {order.user.first_name},

Payment status for your order #{order.id} is now:
{order.payment_status}

- Diverse Delights
"""
    send_email(order.user.email, subject, body)



# Home

@app.route("/")
def home():
    return render_template(
        "home.html",
        products=Product.query.all(),
        categories=Category.query.all(),
        discounted_products=Product.query.filter(Product.discount > 0).all()
    )



# Auth

@app.route("/auth/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirmPassword", "")
        contact_number = request.form.get("contactNumber", "").strip()
        first_name = request.form.get("firstName", "").strip()
        last_name = request.form.get("lastName", "").strip()

        # Required Fields Check

        if not all([email, password, confirm_password, first_name]):
            session['toast'] = {"type": "error", "message": "Please fill all required fields."}
            return redirect(request.url)

        # Email Format Check

        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_regex, email):
            session['toast'] = {"type": "error", "message": "Invalid email format."}
            return redirect(request.url)

        # Email Already Exists Check

        if User.query.filter_by(email=email).first():
            session['toast'] = {"type": "error", "message": "Email already registered!"}
            return redirect(request.url)

        # Password & Confirm Password Match Check

        if password != confirm_password:
            session['toast'] = {"type": "warning", "message": "Passwords do not match!"}
            return redirect(request.url)

        # Password Strength Check

        if len(password) < 8:
            session['toast'] = {"type": "error", "message": "Password must be at least 8 characters long."}
            return redirect(request.url)

        if not re.search(r"[A-Z]", password):
            session['toast'] = {"type": "error", "message": "Password must contain at least one uppercase letter."}
            return redirect(request.url)

        if not re.search(r"[0-9]", password):
            session['toast'] = {"type": "error", "message": "Password must contain at least one number."}
            return redirect(request.url)

        # Contact Number Validation

        if contact_number and not re.match(r"^[0-9]{10}$", contact_number):
            session['toast'] = {"type": "error", "message": "Contact number must be 10 digits."}
            return redirect(request.url)

        # Name Validation

        if not first_name.isalpha():
            session['toast'] = {"type": "error", "message": "First name must contain only letters."}
            return redirect(request.url)
        
        # Last name is optional, but if provided, it should only contain letters.

        if not last_name.isalpha():
            session['toast'] = {"type": "error", "message": "Last name must contain only letters."}
            return redirect(request.url)

        # Create User

        user = User(
            email=email,
            contact_number=contact_number,
            first_name=first_name,
            last_name=last_name,
            password_hash=generate_password_hash(password)
        )

        db.session.add(user)
        db.session.commit()

        send_welcome_email(user)

        session['toast'] = {
            "type": "success",
            "message": "Registration successful! Please log in."
        }
        return redirect("/auth/login")

    return render_template("auth/register.html")



# Login

@app.route("/auth/login", methods=["GET", "POST"])
def login():

    # If user is already logged in, redirect to home

    if request.method == "POST":
        user = User.query.filter_by(email=request.form.get("email")).first()

        # Check if user exists and password is correct

        if user and check_password_hash(user.password_hash, request.form.get("password")):
            session["user"] = {
                "id": user.id,
                "email": user.email,
                "is_admin": user.is_admin
            }
            session['toast'] = {"type": "success", "message": f"Welcome back, {user.first_name}!"}
            return redirect("/")

        session['toast'] = {"type": "error", "message": "Invalid email or password."}
        return redirect(request.url)

    return render_template("auth/login.html")



# Password Reset

@app.route("/auth/reset-password", methods=["GET"])
def reset_password_page():

    step = session.get("reset_step", "email")
    return render_template("auth/reset_password.html", step=step)


# Send OTP and Verify OTP are separated into two steps to enhance security and user experience.

@app.route("/auth/send-otp", methods=["POST"])
def send_otp():
    email = request.form.get("email")

    user = User.query.filter_by(email=email).first()

    # Check if email is registered

    if not user:
        session["toast"] = {"type": "error", "message": "Email not registered."}
        return redirect("/auth/reset-password")

    # Rate Limiting: Prevent multiple OTP requests within 30 seconds

    last_time = session.get("otp_time")
    if last_time and time.time() - last_time < 30:
        session["toast"] = {"type": "error", "message": "Wait before requesting new OTP."}
        return redirect("/auth/reset-password")

    # Generate a secure random 6-digit OTP

    otp = str(random.randint(100000, 999999))

    # Store OTP and related info in session for later verification

    session["reset_email"] = email
    session["reset_otp"] = otp
    session["otp_time"] = time.time()
    session["otp_attempts"] = 0
    session["otp_verified"] = False
    session["reset_step"] = "otp"

    send_otp_email(email, otp)

    session["toast"] = {"type": "success", "message": "OTP sent to email."}
    return redirect("/auth/reset-password")



# Verify OTP

@app.route("/auth/verify-otp", methods=["POST"])
def verify_otp():
    user_otp = request.form.get("otp")
    otp_time = session.get("otp_time")
    
    # OTP Expiration Check
    
    if not otp_time or time.time() - otp_time > 120:
        session["toast"] = {"type": "error", "message": "OTP expired."}
        session["reset_step"] = "email"
        return redirect("/auth/reset-password")

    attempts = session.get("otp_attempts", 0) + 1
    session["otp_attempts"] = attempts

    # Too Many Attempts Check

    if attempts > 5:
        session["toast"] = {"type": "error", "message": "Too many attempts."}
        session["reset_step"] = "email"
        return redirect("/auth/reset-password")
        
    # OTP Verification

    if user_otp == session.get("reset_otp"):
        session["otp_verified"] = True
        session["reset_step"] = "reset"
        session["toast"] = {"type": "success", "message": "OTP verified!"}
    else:
        session["toast"] = {"type": "error", "message": "Invalid OTP."}

    return redirect("/auth/reset-password")



# Final Password Reset after OTP Verification

@app.route("/auth/reset-password", methods=["POST"])
def reset_password():

    # Ensure OTP was verified before allowing password reset

    if not session.get("otp_verified"):
        return redirect("/auth/reset-password")

    password = request.form.get("password")
    confirm = request.form.get("confirmPassword")

    # Password & Confirm Password Match Check

    if password != confirm:
        session["toast"] = {"type": "error", "message": "Passwords do not match."}
        return redirect("/auth/reset-password")

    email = session.get("reset_email")
    user = User.query.filter_by(email=email).first()

    # Update password if user exists

    if user:
        user.password_hash = generate_password_hash(password)
        db.session.commit()

        send_password_changed_email(user)

    session.clear()
    session["toast"] = {"type": "success", "message": "Password reset successful!"}
    return redirect("/auth/login")



# Logout

@app.route("/auth/logout", methods=["POST"])
def logout():
    session.clear()
    session['toast'] = {"type": "info", "message": "You have been logged out."}
    return redirect("/")



# User Profile

@app.route("/profile")
def profile():

    # Ensure user is logged in before accessing profile
    
    if "user" not in session:
        session['toast'] = {"type": "warning", "message": "Please log in to view your profile."}
        return redirect("/auth/login")

    # Fetch fresh user data from database to ensure we have the latest info for profile page
    
    user = db.session.get(User, session["user"]["id"])
    return render_template("profile.html", user=user)



# Products

@app.route("/products")
def products():
    return render_template(
        "products.html",
        products=Product.query.all(),
        categories=Category.query.all()
    )



# Product Details

@app.route("/products/<int:product_id>")
def product_details(product_id):

    product = Product.query.get_or_404(product_id)
    discounted_price = product.price * (1 - product.discount / 100)

    # Check if user has this product in wishlist to show appropriate button state

    user_wishlist_products = []
    if "user" in session:
        user = db.session.get(User, session["user"]["id"])
        if user.wishlist:
            user_wishlist_products = [p.id for p in user.wishlist.products]

    return render_template(
        "product_details.html",
        product=product,
        discounted_price=round(discounted_price, 2),
        reviews=product.review,
        user_wishlist_products=user_wishlist_products
    )



# Reviews

@app.route("/add-review", methods=["POST"])
def add_review():

    # Ensure user is logged in before allowing to submit reviews

    if "user" not in session:
        session['toast'] = {"type": "warning", "message": "You must log in to submit a review."}
        return redirect("/auth/login")

    user_id = session["user"]["id"]
    product_id = request.form.get("product_id")
    rating = int(request.form.get("rating", 0))
    comment = request.form.get("comment", "").strip()

    # Review Comment Validation

    if not (product_id and 1 <= rating <= 5 and comment):
        session['toast'] = {"type": "error", "message": "Please provide a rating and comment."}
        return redirect(request.referrer or f"/products/{product_id}")

    product = Product.query.get_or_404(product_id)

    # Check if user has already reviewed this product.
    # If yes, update the review instead of creating a new one.
    
    existing_review = Review.query.filter_by(user_id=user_id, product_id=product_id).first()
    if existing_review:
        existing_review.rating = rating
        existing_review.comment = comment
        session['toast'] = {"type": "info", "message": "Your review was updated."}
    else:
        new_review = Review(
            user_id=user_id,
            product_id=product_id,
            rating=rating,
            comment=comment
        )
        db.session.add(new_review)
        session['toast'] = {"type": "success", "message": "Review submitted successfully!"}

    db.session.commit()
    return redirect(request.referrer or f"/products/{product_id}")



# Wishlist

@app.route("/wishlist")
def wishlist():

    # Ensure user is logged in before accessing wishlist

    if "user" not in session:
        session['toast'] = {"type": "warning", "message": "Please log in to view your wishlist."}
        return redirect("/auth/login")

    user = db.session.get(User, session["user"]["id"])

    # Ensure wishlist exists for user before rendering

    if not user.wishlist:
        user.wishlist = Wishlist(user_id=user.id)
        db.session.commit()

    return render_template("wishlist.html", wishlist=user.wishlist)



# Add to Wishlist

@app.route("/wishlist/items", methods=["POST"])
def add_wishlist_item():

    # Ensure user is logged in before allowing to add items to wishlist

    if "user" not in session:
        session['toast'] = {"type": "warning", "message": "You must log in to add items to your wishlist."}
        return redirect("/auth/login")

    user = db.session.get(User, session["user"]["id"])
    product = db.session.get(Product, request.form.get("product_id"))

    # Validate product existence before adding to wishlist

    if not product:
        session['toast'] = {"type": "error", "message": "Product not found."}
        return redirect("/products")

    # Ensure wishlist exists for user before adding items

    if not user.wishlist:
        user.wishlist = Wishlist(user_id=user.id)
        db.session.commit()

    # Check if product is already in wishlist to prevent duplicates

    if product not in user.wishlist.products:
        user.wishlist.products.append(product)
        db.session.commit()
        session['toast'] = {"type": "success", "message": f"{product.name} added to wishlist!"}
    else:
        session['toast'] = {"type": "info", "message": f"{product.name} is already in your wishlist."}

    return redirect(request.referrer or "/wishlist")



# Remove from Wishlist

@app.route("/wishlist/items/<int:product_id>", methods=["POST"])
def remove_wishlist_item(product_id):

    # Ensure user is logged in before allowing to remove items from wishlist

    if "user" not in session:
        session['toast'] = {"type": "warning", "message": "You must log in to remove items."}
        return redirect("/auth/login")

    # Check for method override to allow DELETE via POST

    if request.form.get("_method") == "DELETE":
        user = db.session.get(User, session["user"]["id"])
        product = db.session.get(Product, product_id)

        # Validate product existence before attempting to remove from wishlist

        if user.wishlist and product in user.wishlist.products:
            user.wishlist.products.remove(product)
            db.session.commit()
            session['toast'] = {"type": "success", "message": f"{product.name} removed from wishlist."}
        else:
            session['toast'] = {"type": "info", "message": "Product was not in your wishlist."}

    return redirect(request.referrer or "/wishlist")



# Cart

@app.route("/cart")
def cart():

    # Ensure user is logged in before accessing cart

    if "user" not in session:
        session['toast'] = {"type": "warning", "message": "Please log in to view your cart."}
        return redirect("/auth/login")

    user = db.session.get(User, session["user"]["id"])

    # Ensure cart exists for user before rendering

    if not user.cart:
        user.cart = Cart(user_id=user.id)
        db.session.commit()

    # Calculate grand total with discounts applied on the server side to prevent tampering

    grand_total = sum(
        (item.product.price * (1 - item.product.discount / 100)) * item.quantity
        for item in user.cart.items
    )

    # Pass Razorpay key to template

    razorpay_key_id = os.getenv("RAZORPAY_KEY_ID")

    return render_template(
        "cart.html",
        cart=user.cart,
        grand_total=round(grand_total, 2),
        razorpay_key_id=razorpay_key_id
    )



# Add to Cart

@app.route("/cart/items", methods=["POST"])
def add_cart_item():

    # Ensure user is logged in before allowing to add items to cart

    if "user" not in session:
        session['toast'] = {"type": "warning", "message": "You must log in to add items to your cart."}
        return redirect("/auth/login")

    user = db.session.get(User, session["user"]["id"])
    product = db.session.get(Product, request.form.get("product_id"))
    quantity = int(request.form.get("quantity", 1))

    # Validate quantity
    
    if quantity <= 0:
        session['toast'] = {"type": "error", "message": "Quantity must be at least 1."}
        return redirect(request.referrer or f"/products/{product.id}")

    # Validate product existence before adding to cart
    
    if not product:
        session['toast'] = {"type": "error", "message": "Product not found."}
        return redirect("/products")

    # Ensure cart exists for user before adding items

    if not user.cart:
        user.cart = Cart(user_id=user.id)
        db.session.commit()

    # Check if the product is already in the cart.
    # If yes, update the quantity instead of adding a new entry.

    existing = CartItem.query.filter_by(
        cart_id=user.cart.id,
        product_id=product.id
    ).first()

    if existing:
        existing.quantity += quantity
        session['toast'] = {"type": "info", "message": f"Updated {product.name} quantity in your cart."}
    else:
        db.session.add(CartItem(
            cart_id=user.cart.id,
            product_id=product.id,
            quantity=quantity
        ))
        session['toast'] = {"type": "success", "message": f"{product.name} added to cart!"}

    db.session.commit()
    return redirect("/cart")



# Remove from Cart

@app.route("/cart/items/<int:item_id>/remove", methods=["POST"])
def remove_from_cart(item_id):

    # Ensure user is logged in before allowing to remove items from cart

    if "user" not in session:
        session['toast'] = {
            "type": "warning",
            "message": "You must log in to remove items."
        }
        return redirect("/auth/login")
    
    item = CartItem.query.get_or_404(item_id)

    # Ensure the cart item belongs to the logged-in user to prevent unauthorized deletion

    if item.cart.user_id != session["user"]["id"]:
        session['toast'] = {
            "type": "error",
            "message": "Cannot remove this item."
        }
        return redirect("/cart")

    # Get product name before deleting to display in toast
    
    product_name = item.product.name

    db.session.delete(item)
    db.session.commit()

    session['toast'] = {
        "type": "success",
        "message": f"{product_name} removed from cart."
    }

    return redirect("/cart")


# Razorpay Order Creation Endpoint

@app.route("/create-razorpay-order", methods=["POST"])
def create_razorpay_order():
    if "user" not in session:
        return {"error": "Login required"}, 401

    user = db.session.get(User, session["user"]["id"])

    if not user.cart or not user.cart.items:
        return {"error": "Cart is empty"}, 400

    # Recalculate total on server to prevent tampering
    total = sum(
        (item.product.price * (1 - item.product.discount / 100)) * item.quantity
        for item in user.cart.items
    )

    # Validate total amount before creating Razorpay order

    if total <= 0:
        return {"error": "Invalid cart total"}, 400

    # Razorpay expects amount in paise (1 INR = 100 paise)

    amount_in_paise = int(round(total * 100))

    # Create Razorpay order with capture set to 1 for automatic capture after payment

    razorpay_order = client.order.create({
        "amount": amount_in_paise,
        "currency": "INR",
        "payment_capture": 1
    })

    return razorpay_order

# Orders

@app.route("/orders", methods=["GET", "POST"])
def orders():

    # Ensure user is logged in before accessing orders

    if "user" not in session:
        session['toast'] = {
            "type": "warning",
            "message": "Please log in to view your orders."
        }
        return redirect("/auth/login")

    user = db.session.get(User, session["user"]["id"])

    # Handle new order creation on POST request

    if request.method == "POST":

        # Ensure cart is not empty before creating an order

        if not user.cart or not user.cart.items:
            session['toast'] = {
                "type": "error",
                "message": "Your cart is empty."
            }
            return redirect("/cart")

        # Extract and validate shipping and payment details from the request

        # First, try to get data from JSON payload if it's an AJAX request.

        if request.is_json:
            data = request.get_json()
            payment_method = data.get("payment_method", "COD")
            full_name = (data.get("full_name") or "").strip()
            phone = (data.get("phone") or "").strip()
            address = (data.get("address") or "").strip()
            city = (data.get("city") or "").strip()
            state = (data.get("state") or "").strip()
            pincode = (data.get("pincode") or "").strip()
        
        # If not JSON, fallback to form data (for non-AJAX requests)

        else:
            payment_method = request.form.get("payment_method", "COD")
            full_name = (request.form.get("full_name") or "").strip()
            phone = (request.form.get("phone") or "").strip()
            address = (request.form.get("address") or "").strip()
            city = (request.form.get("city") or "").strip()
            state = (request.form.get("state") or "").strip()
            pincode = (request.form.get("pincode") or "").strip()

        # Required Fields Validation

        if not all([full_name, phone, address, city, state, pincode]):
            session['toast'] = {
                "type": "error",
                "message": "Please fill all shipping details."
            }
            return redirect("/cart")

        # Contact Number Validation

        if not re.match(r"^[0-9]{10}$", phone):
            session['toast'] = {
                "type": "error",
                "message": "Invalid phone number."
            }
            return redirect("/cart")

        # Pincode Validation

        if not re.match(r"^[0-9]{6}$", pincode):
            session['toast'] = {
                "type": "error",
                "message": "Invalid pincode."
            }
            return redirect("/cart")

        cart = user.cart

        # Validate cart items before creating order to ensure no invalid quantities or stock issues

        for item in cart.items:
            if item.quantity <= 0:
                session['toast'] = {
                    "type": "error",
                    "message": "Invalid quantity detected."
                }
                return redirect("/cart")

            # Check if product still has enough stock before creating order to prevent overselling

            if item.quantity > item.product.stock:
                session['toast'] = {
                    "type": "error",
                    "message": f"{item.product.name} does not have enough stock."
                }
                return redirect("/cart")

        # Calculate total amount with discounts applied on the server side to prevent tampering

        total = sum(
            (item.product.price * (1 - item.product.discount / 100)) * item.quantity
            for item in cart.items
        )

        # Safe default payment status based on payment method.

        payment_status = "Pending"
        
        # Create Order
        
        order = Order(
            user_id=user.id,
            total_amount=round(total, 2),
            payment_method=payment_method,
            payment_status=payment_status,
            order_status="Pending",
            full_name=full_name,
            phone=phone,
            address=address,
            city=city,
            state=state,
            pincode=pincode,
        )

        db.session.add(order)
        db.session.flush()

        # Create Order Items

        for item in cart.items:
            discounted_price = item.product.price * (1 - item.product.discount / 100)

            order_item = OrderItem(
                order_id=order.id,
                product_name=item.product.name,
                price=round(discounted_price, 2),
                quantity=item.quantity,
                product_image=item.product.image_url,
                product_id=item.product.id
            )

            # Deduct stock for the product safely within the same transaction to prevent overselling

            item.product.stock -= item.quantity

            db.session.add(order_item)

        # Clear Cart after creating order

        for item in cart.items:
            db.session.delete(item)

        db.session.commit()
        
        send_order_confirmation_email(user, order)
        
        session['toast'] = {
            "type": "success",
            "message": f"Order #{order.id} placed successfully!"
        }

        # Redirect to orders page after placing order.
        # If it's an AJAX request, return JSON with redirect URL.
        
        if request.is_json:
            return {"redirect_url": url_for("orders")}
        else:
            return redirect("/orders")

    # For GET request, display user's orders

    user_orders = (
        Order.query
        .filter_by(user_id=user.id)
        .order_by(Order.created_at.desc())
        .all()
    )

    return render_template("orders.html", orders=user_orders)



# Admin Dashboard and Management

# Admin routes are protected with @admin_required decorator to ensure only admins can access them.

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):

        # Check if user is logged in

        if "user" not in session:
            session['toast'] = {"type": "warning", "message": "Please log in first."}
            return redirect("/auth/login")

        # Check if logged-in user is an admin

        if not session["user"]["is_admin"]:
            session['toast'] = {"type": "error", "message": "Admin access required."}
            return redirect("/")
            
        # If both checks pass, proceed to the admin route function
        
        return f(*args, **kwargs)
    return wrapper



# Admin Dashboard

@app.route("/admin")
@admin_required
def admin_dashboard():

    # Aggregate metrics for dashboard display

    total_orders = Order.query.count()
    total_revenue = sum(order.total_amount for order in Order.query.all())
    
    total_users = User.query.count()
    total_admins = User.query.filter_by(is_admin=True).count()
    total_clients = total_users - total_admins

    total_products = Product.query.count()
    total_categories = Category.query.count()

    total_pending = Order.query.filter_by(order_status="Pending").count()
    total_processing = Order.query.filter_by(order_status="Processing").count()
    total_shipped = Order.query.filter_by(order_status="Shipped").count()
    total_delivered = Order.query.filter_by(order_status="Delivered").count()

    # Compile all metrics into a dictionary to pass to the template for rendering

    metrics = {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "total_users": total_users,
        "total_admins": total_admins,
        "total_clients": total_clients,
        "total_products": total_products,
        "total_categories": total_categories,
        "total_pending": total_pending,
        "total_processing": total_processing,
        "total_shipped": total_shipped,
        "total_delivered": total_delivered
    }

    return render_template("/admin/admin_dashboard.html", metrics=metrics)



# Admin Category Management

@app.route("/admin/categories")
@admin_required
def admin_categories():

    # Fetch all categories ordered by creation date to display in admin category management page

    categories = Category.query.order_by(Category.created_at.desc()).all()

    selected_category = None
    selected_delete_category = None

    edit_id = request.args.get("edit_category_id")
    delete_id = request.args.get("delete_category_id")

    # If edit_id is present in query parameters, fetch the corresponding category to pre-fill the edit form in the template

    if edit_id:
        selected_category = Category.query.get(edit_id)

    # If delete_id is present in query parameters, fetch the corresponding category to show details in the delete confirmation modal in the template

    if delete_id:
        selected_delete_category = Category.query.get(delete_id)

    return render_template(
        "/admin/admin_manage_categories.html",
        categories=categories,
        selected_category=selected_category,
        selected_delete_category=selected_delete_category
    )


# Admin Create Category

@app.route("/admin/categories/create", methods=["POST"])
@admin_required
def admin_create_category():

    # Get category name from form and strip whitespace to prevent creating categories with just spaces

    category_name = request.form.get("category").strip()

    # Validate that category name is not empty after stripping whitespace to ensure meaningful category names

    if not category_name:
        session['toast'] = {"type": "error", "message": "Category name cannot be empty."}
        return redirect("/admin/categories")

    # Check if a category with the same name already exists to prevent duplicates

    existing = Category.query.filter_by(category=category_name).first()
    if existing:
        session['toast'] = {"type": "warning", "message": "Category already exists."}

    # If validation passes and no duplicate exists, create the new category and save to database

    else:
        new_cat = Category(category=category_name)
        db.session.add(new_cat)
        db.session.commit()
        session['toast'] = {"type": "success", "message": "Category created successfully."}

    return redirect("/admin/categories")



# Admin Edit Category

@app.route("/admin/categories/<int:category_id>/edit", methods=["POST"])
@admin_required
def admin_edit_category(category_id):

    # Fetch the category to be edited using the provided category_id. If not found, return a 404 error.

    category = Category.query.get_or_404(category_id)
    new_name = request.form.get("category", "").strip()

    # Validate that the new category name is not empty after stripping whitespace to ensure meaningful category names

    if not new_name:
        session['toast'] = {
            "type": "error",
            "message": "Category name cannot be empty."
        }
        return redirect("/admin/categories")

    # Check if another category with the same new name already exists (excluding the current category being edited) to prevent duplicates

    existing = Category.query.filter(
        Category.category == new_name,
        Category.id != category.id
    ).first()

    # If a duplicate category name exists, show a warning message. Otherwise, update the category name and save changes to the database.

    if existing:
        session['toast'] = {
            "type": "warning",
            "message": "Another category with this name already exists."
        }
    else:
        category.category = new_name
        db.session.commit()
        session['toast'] = {
            "type": "success",
            "message": "Category updated successfully."
        }

    return redirect("/admin/categories")



# Admin Delete Category

@app.route("/admin/categories/<int:category_id>/delete", methods=["POST"])
@admin_required
def admin_delete_category(category_id):

    # Fetch the category to be deleted using the provided category_id. If not found, return a 404 error.

    category = Category.query.get_or_404(category_id)
    
    # Attempt to delete the category. If the category is linked to existing products, it will raise an exception due to foreign key constraints. In that case, rollback the transaction and show an error message.
    
    try:
        db.session.delete(category)
        db.session.commit()

        session['toast'] = {
            "type": "success",
            "message": "Category deleted successfully."
        }

    except Exception:
        db.session.rollback()
        session['toast'] = {
            "type": "error",
            "message": "Cannot delete category. It may be linked to existing products."
        }

    return redirect("/admin/categories")



# Admin Product Management

@app.route("/admin/products")
@admin_required
def admin_products():

    # Fetch all products ordered by creation date to display in admin product management page

    products = Product.query.order_by(Product.created_at.desc()).all()
    categories = Category.query.all()

    # Selected product for editing based on query parameter. If edit_product_id is present in the URL, fetch that product to pre-fill the edit form in the template.

    edit_id = request.args.get("edit_product_id")
    selected_product = Product.query.get(edit_id) if edit_id else None

    # Selected product for deletion based on query parameter. If delete_product_id is present in the URL, fetch that product to show details in the delete confirmation modal in the template.

    delete_id = request.args.get("delete_product_id")
    selected_delete_product = Product.query.get(delete_id) if delete_id else None

    return render_template(
        "/admin/admin_manage_products.html",
        products=products,
        categories=categories,
        selected_product=selected_product,
        selected_delete_product=selected_delete_product
    )



# Admin Create Product

@app.route("/admin/products/create", methods=["GET", "POST"])
@admin_required
def admin_create_product():

    # Fetch all categories to show in the category dropdown when creating a new product

    categories = Category.query.all()
    
    # Handle form submission for creating a new product.

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price = request.form.get("price")
        discount = request.form.get("discount") or 0
        stock = request.form.get("stock") or 0
        category_id = request.form.get("category_id")
        image_url = request.form.get("image_url", "").strip()

        # Basic validation to ensure required fields are provided and not just whitespace.

        if not (name and description and price and category_id):
            session['toast'] = {
                "type": "error",
                "message": "All required fields must be filled."
            }
            return redirect("/admin/products")

        # Attempt to create a new product with the provided details.

        try:
            product = Product(
                name=name,
                description=description,
                price=float(price),
                discount=float(discount),
                stock=int(stock),
                category_id=int(category_id),
                image_url=image_url or "https://via.placeholder.com/150"
            )

            db.session.add(product)
            db.session.commit()

            session['toast'] = {
                "type": "success",
                "message": "Product created successfully."
            }

        # Handle value errors that may occur during type conversion for price, discount, and stock.

        except Exception:
            db.session.rollback()
            session['toast'] = {
                "type": "error",
                "message": "Failed to create product."
            }

        return redirect("/admin/products")
    
    return render_template("/admin/admin_create_product.html", categories=categories)



# Admin Edit Product

@app.route("/admin/products/<int:product_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_edit_product(product_id):

    # Fetch the product to be edited using the provided product_id. If not found, return a 404 error.

    product = Product.query.get_or_404(product_id)
    categories = Category.query.all()

    # Handle form submission for editing the product details.

    if request.method == "POST":
        try:
            name = request.form.get("name", "").strip()
            description = request.form.get("description", "").strip()
            price = request.form.get("price")
            category_id = request.form.get("category_id")

            # Basic validation to ensure required fields are provided and not just whitespace.

            if not (name and description and price and category_id):
                session['toast'] = {
                    "type": "error",
                    "message": "All required fields must be filled."
                }
                return redirect("/admin/products")

            # Update product details with the provided values.

            product.name = name
            product.description = description
            product.price = float(price)
            product.discount = float(request.form.get("discount") or 0)
            
            # Validate stock value to ensure it's a non-negative integer before updating the product.
            
            stock = int(request.form.get("stock") or 0)
            if stock < 0:
                session['toast'] = {
                    "type": "error",
                    "message": "Stock cannot be negative."
                }
                return redirect("/admin/products")

            product.stock = stock
            product.category_id = int(category_id)
            
            image_url = request.form.get("image_url", "").strip()
            product.image_url = image_url or "https://via.placeholder.com/150"

            db.session.commit()

            session['toast'] = {
                "type": "success",
                "message": "Product updated successfully."
            }
            
        # Handle value errors that may occur during type conversion for price, discount, and stock.
        
        except ValueError:
            db.session.rollback()
            session['toast'] = {
                "type": "error",
                "message": "Invalid numeric values provided."
            }

        # Handle any other exceptions that may occur during the update process and rollback the transaction to maintain data integrity.

        except Exception:
            db.session.rollback()
            session['toast'] = {
                "type": "error",
                "message": "Something went wrong while updating the product."
            }

        return redirect("/admin/products")

    return render_template(
        "/admin/admin_manage_products.html",
        products=[product],
        categories=categories,
        selected_product=product
    )



# Admin Delete Product

@app.route("/admin/products/<int:product_id>/delete", methods=["POST"])
@admin_required
def admin_delete_product(product_id):

    # Fetch the product to be deleted using the provided product_id. If not found, return a 404 error.

    product = Product.query.get_or_404(product_id)

    # Attempt to delete the product.

    try:
        db.session.delete(product)
        db.session.commit()

        session['toast'] = {
            "type": "success",
            "message": "Product deleted successfully."
        }

    # Handle exceptions that may occur during deletion, such as foreign key constraints if the product is linked to existing orders. Rollback the transaction and show an error message in that case.

    except Exception:
        db.session.rollback()
        session['toast'] = {
            "type": "error",
            "message": "Cannot delete product. It may be linked to existing orders."
        }

    return redirect("/admin/products")



# Admin Order Management

@app.route("/admin/orders")
@admin_required
def admin_orders():

    # Fetch

    all_orders = Order.query.order_by(Order.created_at.desc()).all()

    # Separate active orders (Pending, Processing, Shipped) from completed orders (Delivered) to display in different sections in the admin order management page.

    active_orders = [o for o in all_orders if o.order_status in ["Pending", "Processing", "Shipped"]]
    completed_orders = [o for o in all_orders if o.order_status == "Delivered"]

    return render_template(
        "/admin/admin_manage_orders.html",
        active_orders=active_orders,
        completed_orders=completed_orders
    )



# Admin Order Details

@app.route("/admin/orders/<int:order_id>")
@admin_required
def admin_order_details(order_id):

    # Fetch the order using the provided order_id. If not found, return a 404 error.
    
    order = Order.query.get_or_404(order_id)
    return render_template("/admin/admin_order_details.html", order=order)



# Admin Update Order Status

@app.route("/admin/update-order-status/<int:order_id>", methods=["POST"])
@admin_required
def update_order_status(order_id):

    # Fetch the order to be updated using the provided order_id. If not found, return a 404 error.

    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status", "").strip()

    # Validate the new order status against a list of allowed statuses to ensure only valid statuses can be set for an order.

    allowed_statuses = ["Pending", "Processing", "Shipped", "Delivered"]

    if new_status not in allowed_statuses:
        session['toast'] = {
            "type": "error",
            "message": "Invalid order status."
        }
        return redirect("/admin/orders")

    # Attempt to update the order status.

    try:
        order.order_status = new_status
        db.session.commit()

        session['toast'] = {
            "type": "success",
            "message": f"Order #{order.id} updated to {new_status}."
        }

    # Handle exceptions that may occur during the update process and rollback the transaction to maintain data integrity.

    except Exception:
        db.session.rollback()
        session['toast'] = {
            "type": "error",
            "message": "Failed to update order status."
        }

    return redirect("/admin/orders")



# Admin Update Payment Status

@app.route("/admin/orders/<int:order_id>/payment", methods=["POST"])
@admin_required
def update_payment_status(order_id):

    # Fetch the order to be updated using the provided order_id. If not found, return a 404 error.

    order = Order.query.get_or_404(order_id)
    new_payment_status = request.form.get("payment_status", "").strip()

    # Validate the new payment status against a list of allowed statuses to ensure only valid payment statuses can be set for an order.

    allowed_payment_statuses = ["Pending", "Paid", "Failed", "Refunded"]

    # If the new payment status is not in the list of allowed statuses, show an error message and redirect back to the order details page without making any changes to the database.

    if new_payment_status not in allowed_payment_statuses:
        session['toast'] = {
            "type": "error",
            "message": "Invalid payment status."
        }
        return redirect(f"/admin/orders/{order_id}")

    # Attempt to update the payment status of the order.
    
    try:
        order.payment_status = new_payment_status
        db.session.commit()

        session['toast'] = {
            "type": "success",
            "message": f"Payment status updated to {new_payment_status}."
        }

    # Handle exceptions that may occur during the update process and rollback the transaction to maintain data integrity.

    except Exception:
        db.session.rollback()
        session['toast'] = {
            "type": "error",
            "message": "Failed to update payment status."
        }

    return redirect(f"/admin/orders/{order_id}")



# Run the Flask application in debug mode for development.
# In production, debug should be set to False for security reasons.

if __name__ == "__main__":
    app.run(debug=True)