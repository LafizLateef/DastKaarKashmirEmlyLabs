from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import os
import time
import uuid
import secrets
from datetime import datetime
from groq import Groq
import json
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

USERS_FILE = os.path.join(BASE_DIR, "users.json")
BUYERS_FILE = os.path.join(BASE_DIR, "Json", "buyers.json")
MANUFACTURERS_FILE = os.path.join(BASE_DIR, "Json", "manufacturers.json")
CACHE_FILE = os.path.join(BASE_DIR, "ai_cache.json")
API_FILE = os.path.join(BASE_DIR, "Api.txt")
SECRET_KEY_FILE = os.path.join(BASE_DIR, "secret.key")
PRODUCTS_FILE = os.path.join(BASE_DIR, "products.json")
MESSAGES_FILE = os.path.join(BASE_DIR, "messages.json")
PRODUCT_IMAGE_DIR = os.path.join(BASE_DIR, "static", "images", "products")

os.makedirs(PRODUCT_IMAGE_DIR, exist_ok=True)

# ==========================
# App secret key (generated once, kept out of source control)
# ==========================
if not os.path.exists(SECRET_KEY_FILE):
    with open(SECRET_KEY_FILE, "w") as f:
        f.write(secrets.token_hex(32))

with open(SECRET_KEY_FILE, "r") as f:
    app.secret_key = f.read().strip()

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") == "production",
    MAX_CONTENT_LENGTH=8 * 1024 * 1024,
)


@app.errorhandler(413)
def file_too_large(_error):
    return jsonify({
        "success": False,
        "message": "Uploaded file is too large (8MB max)."
    }), 413

with open("Api.txt", "r") as f:
    apikey = f.read().strip()

client = Groq(
    api_key=apikey
)

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump([], f, indent=4)

if not os.path.exists(PRODUCTS_FILE):
    _seed_owner = None
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            _existing_users = json.load(f)
        if _existing_users:
            _seed_owner = _existing_users[0]["email"]

    _demo_products = [
        ("Handwoven Pashmina Shawl", "Pashmina", 240, 18, "Hand-spun and hand-woven pure Pashmina wool shawl, dyed using traditional natural techniques."),
        ("Hand-Carved Walnut Box", "Walnut Wood", 85, 22, "Intricately hand-carved walnut wood box featuring traditional Kashmiri motifs."),
        ("Sozni Embroidered Stole", "Pashmina", 165, 6, "Fine wool stole finished with delicate Sozni needlework."),
        ("Kashmiri Silk Carpet", "Carpets", 620, 4, "Hand-knotted silk carpet with a classic Kashmiri floral design."),
        ("Engraved Copper Samovar", "Copperware", 145, 0, "Traditional hand-engraved copper samovar for serving Kahwa."),
        ("Papier Mâché Jewellery Box", "Papier Mâché", 38, 30, "Hand-painted papier mâché jewellery box with gold leaf detailing."),
        ("Namda Wool Rug", "Namda", 110, 5, "Felted wool rug hand-embroidered with chain stitch florals."),
        ("Willow Wicker Basket", "Willow Wicker", 29, 40, "Handwoven willow wicker basket, durable and lightweight."),
    ]

    seeded = []
    if _seed_owner:
        for name, category, price, stock, description in _demo_products:
            seeded.append({
                "id": str(uuid.uuid4()),
                "owner_email": _seed_owner,
                "name": name,
                "category": category,
                "price": price,
                "stock": stock,
                "description": description,
                "created_at": datetime.utcnow().isoformat()
            })

    with open(PRODUCTS_FILE, "w") as f:
        json.dump(seeded, f, indent=4)

if not os.path.exists(MESSAGES_FILE):
    with open(MESSAGES_FILE, "w") as f:
        json.dump({}, f, indent=4)


# ==========================
# Helper Functions
# ==========================


def hash_password(password):
    """Legacy unsalted hash, kept only to verify pre-existing accounts."""
    return hashlib.sha256(password.encode()).hexdigest()


def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)


def public_user(user):
    """Strip sensitive fields before the user dict is exposed to templates/session."""
    return {k: v for k, v in user.items() if k != "password"}


def load_products():
    with open(PRODUCTS_FILE, "r") as f:
        return json.load(f)


def save_products(products):
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(products, f, indent=4)


def stock_tag(stock):
    if stock <= 0:
        return "Out of Stock", "tag-danger"
    if stock < 10:
        return "Low Stock", "tag-warning"
    return "In Stock", "tag-success"


def detect_image_extension(file_storage):
    """Sniff the real file type from its magic bytes rather than trusting the filename/extension."""
    header = file_storage.stream.read(8)
    file_storage.stream.seek(0)

    if header.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"

    return None


def save_product_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None

    ext = detect_image_extension(file_storage)
    if not ext:
        return None

    filename = f"{uuid.uuid4().hex}.{ext}"
    file_storage.save(os.path.join(PRODUCT_IMAGE_DIR, filename))

    return f"images/products/{filename}"


def delete_product_image(relative_path):
    if not relative_path:
        return

    static_root = os.path.normpath(os.path.join(BASE_DIR, "static"))
    abs_path = os.path.normpath(os.path.join(static_root, relative_path))

    # Guard against a stored path ever escaping the static/ directory.
    if not abs_path.startswith(static_root):
        return

    if os.path.exists(abs_path):
        try:
            os.remove(abs_path)
        except OSError:
            pass


def load_messages():
    with open(MESSAGES_FILE, "r") as f:
        return json.load(f)


def save_messages(store):
    with open(MESSAGES_FILE, "w") as f:
        json.dump(store, f, indent=4)


# ==========================
# Basic login throttling (per email, in-memory)
# ==========================
LOGIN_ATTEMPTS = {}
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 300


def is_locked_out(email):
    entry = LOGIN_ATTEMPTS.get(email)
    if not entry:
        return False
    count, first_attempt = entry
    if count < MAX_LOGIN_ATTEMPTS:
        return False
    if time.time() - first_attempt > LOGIN_LOCKOUT_SECONDS:
        LOGIN_ATTEMPTS.pop(email, None)
        return False
    return True


def register_failed_login(email):
    count, first_attempt = LOGIN_ATTEMPTS.get(email, (0, time.time()))
    LOGIN_ATTEMPTS[email] = (count + 1, first_attempt)


def clear_failed_login(email):
    LOGIN_ATTEMPTS.pop(email, None)

@app.route("/")
def login_page():
    return render_template("login.html")


@app.route("/signup")
def signup_page():
    return render_template("signup.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    return render_template(
        "dashboard.html",
        user=session["user"]
    )


@app.route("/marketplace")
def marketplace():

    if "user" not in session:
        return redirect("/")

    return render_template(
        "marketplace.html",
        user=session["user"]
    )


@app.route("/marketplace/product")
def product_detail():
    if "user" not in session:
        return redirect("/")

    return render_template(
        "product-detail.html",
        user=session["user"]
    )


@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect("/")

    return render_template(
        "profile.html",
        user=session["user"]
    )


@app.route("/products")
def products():
    if "user" not in session:
        return redirect("/")

    owner_email = session["user"]["email"]
    all_products = load_products()

    my_products = []
    for p in all_products:
        if p.get("owner_email") != owner_email:
            continue
        label, cls = stock_tag(p.get("stock", 0))
        image_url = url_for("static", filename=p["image"]) if p.get("image") else ""
        my_products.append({**p, "stock_label": label, "stock_class": cls, "image_url": image_url})

    return render_template(
        "products.html",
        user=session["user"],
        products=my_products
    )


def _validate_product_payload(data):
    name = (data.get("name") or "").strip()
    category = (data.get("category") or "").strip()
    description = (data.get("description") or "").strip()

    if not name or not category:
        return None, "Product name and category are required."

    try:
        price = float(data.get("price"))
        stock = int(data.get("stock"))
    except (TypeError, ValueError):
        return None, "Price and stock must be valid numbers."

    if price < 0 or stock < 0:
        return None, "Price and stock cannot be negative."

    return {
        "name": name,
        "category": category,
        "price": price,
        "stock": stock,
        "description": description
    }, None


def _product_response(product):
    label, cls = stock_tag(product["stock"])
    image_url = url_for("static", filename=product["image"]) if product.get("image") else ""
    return {**product, "stock_label": label, "stock_class": cls, "image_url": image_url}


@app.route("/api/products", methods=["POST"])
def create_product():
    if "user" not in session:
        return jsonify({"success": False, "message": "Please login first."}), 401

    data = request.form if request.form else (request.get_json(silent=True) or {})
    fields, error = _validate_product_payload(data)

    if error:
        return jsonify({"success": False, "message": error}), 400

    image_path = None
    uploaded = request.files.get("images")

    if uploaded and uploaded.filename:
        image_path = save_product_image(uploaded)
        if image_path is None:
            return jsonify({"success": False, "message": "Please upload a JPG or PNG image."}), 400

    product = {
        "id": str(uuid.uuid4()),
        "owner_email": session["user"]["email"],
        "created_at": datetime.utcnow().isoformat(),
        "image": image_path,
        **fields
    }

    all_products = load_products()
    all_products.append(product)
    save_products(all_products)

    return jsonify({
        "success": True,
        "product": _product_response(product)
    })


@app.route("/api/products/<product_id>", methods=["PUT"])
def update_product(product_id):
    if "user" not in session:
        return jsonify({"success": False, "message": "Please login first."}), 401

    data = request.form if request.form else (request.get_json(silent=True) or {})
    fields, error = _validate_product_payload(data)

    if error:
        return jsonify({"success": False, "message": error}), 400

    all_products = load_products()
    owner_email = session["user"]["email"]

    for p in all_products:
        if p["id"] == product_id and p.get("owner_email") == owner_email:
            uploaded = request.files.get("images")

            if uploaded and uploaded.filename:
                new_image = save_product_image(uploaded)
                if new_image is None:
                    return jsonify({"success": False, "message": "Please upload a JPG or PNG image."}), 400
                delete_product_image(p.get("image"))
                p["image"] = new_image

            p.update(fields)
            save_products(all_products)

            return jsonify({
                "success": True,
                "product": _product_response(p)
            })

    return jsonify({"success": False, "message": "Product not found."}), 404


@app.route("/api/products/<product_id>", methods=["DELETE"])
def delete_product(product_id):
    if "user" not in session:
        return jsonify({"success": False, "message": "Please login first."}), 401

    all_products = load_products()
    owner_email = session["user"]["email"]

    target = next(
        (p for p in all_products if p["id"] == product_id and p.get("owner_email") == owner_email),
        None
    )

    if target is None:
        return jsonify({"success": False, "message": "Product not found."}), 404

    delete_product_image(target.get("image"))

    remaining = [p for p in all_products if p["id"] != product_id]

    save_products(remaining)

    return jsonify({"success": True})


@app.route("/orders")
def orders():
    if "user" not in session:
        return redirect("/")

    return render_template(
        "orders.html",
        user=session["user"]
    )


CHAT_CONTACTS = [
    "Nordic Home Co.",
    "Ahmed Textiles",
    "Al Noor Traders",
    "Berlin Craft House",
    "Dubai Home Interiors"
]

DEFAULT_MESSAGE_SEED = {
    "Nordic Home Co.": [
        {
            "sender": "them",
            "text": "Hej! We reviewed the catalogue and love the Pashmina collection.",
            "time": "10:30 AM",
            "translation": 'Original (Swedish): "Hej! Vi har granskat katalogen och alskar Pashmina-kollektionen."'
        },
        {
            "sender": "me",
            "text": "Thank you! We can offer wholesale pricing for orders above 50 units.",
            "time": "10:34 AM"
        },
        {
            "sender": "them",
            "text": "That works well for us. Could you also share the shipping timeline?",
            "time": "10:42 AM",
            "translation": 'Original (Swedish): "Det fungerar bra for oss. Kan du ocksa dela leveranstiden?"'
        }
    ]
}


def get_thread(owner_email, contact):
    store = load_messages()

    if owner_email not in store:
        store[owner_email] = {c: list(msgs) for c, msgs in DEFAULT_MESSAGE_SEED.items()}
        save_messages(store)

    return store, store[owner_email].get(contact, [])


@app.route("/messages")
def messages():
    if "user" not in session:
        return redirect("/")

    owner_email = session["user"]["email"]
    active_contact = request.args.get("contact", CHAT_CONTACTS[0])

    if active_contact not in CHAT_CONTACTS:
        active_contact = CHAT_CONTACTS[0]

    store, thread = get_thread(owner_email, active_contact)
    user_threads = store[owner_email]

    previews = {}
    for contact in CHAT_CONTACTS:
        contact_thread = user_threads.get(contact, [])
        if contact_thread:
            last = contact_thread[-1]
            previews[contact] = {"text": last["text"], "time": last["time"]}
        else:
            previews[contact] = {"text": "No messages yet", "time": ""}

    return render_template(
        "messages.html",
        user=session["user"],
        contacts=CHAT_CONTACTS,
        active_contact=active_contact,
        messages=thread,
        previews=previews
    )


@app.route("/api/messages/<contact>")
def get_messages(contact):
    if "user" not in session:
        return jsonify({"success": False}), 401

    if contact not in CHAT_CONTACTS:
        return jsonify({"success": False, "message": "Unknown conversation."}), 404

    _, thread = get_thread(session["user"]["email"], contact)

    return jsonify({"success": True, "messages": thread})


@app.route("/api/messages/<contact>", methods=["POST"])
def send_message(contact):
    if "user" not in session:
        return jsonify({"success": False, "message": "Please login first."}), 401

    if contact not in CHAT_CONTACTS:
        return jsonify({"success": False, "message": "Unknown conversation."}), 404

    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"success": False, "message": "Message cannot be empty."}), 400

    if len(text) > 2000:
        return jsonify({"success": False, "message": "Message is too long."}), 400

    owner_email = session["user"]["email"]
    store, thread = get_thread(owner_email, contact)

    message = {
        "sender": "me",
        "text": text,
        "time": datetime.now().strftime("%I:%M %p").lstrip("0")
    }

    thread.append(message)
    store[owner_email][contact] = thread
    save_messages(store)

    return jsonify({"success": True, "message": message})


@app.route("/analytics")
def analytics():
    if "user" not in session:
        return redirect("/")

    return render_template(
        "analytics.html",
        user=session["user"]
    )


@app.route("/ai")
def ai():
    if "user" not in session:
        return redirect("/")

    return render_template(
        "ai.html",
        user=session["user"]
    )


@app.route("/verification")
def verification():
    if "user" not in session:
        return redirect("/")

    return render_template(
        "verification.html",
        user=session["user"]
    )


@app.route("/settings")
def settings():
    if "user" not in session:
        return redirect("/")

    return render_template(
        "settings.html",
        user=session["user"]
    )


@app.route("/styleguide")
def styleguide():
    if "user" not in session:
        return redirect("/")

    return render_template(
        "styleguide.html",
        user=session["user"]
    )

@app.route("/signup", methods=["POST"])
def signup():

    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = (data.get("role") or "").strip()
    phone = (data.get("phone") or "").strip()

    if not name or not email or not password or not role:
        return jsonify({
            "success": False,
            "message": "All required fields must be filled in"
        }), 400

    if "@" not in email or "." not in email.split("@")[-1]:
        return jsonify({
            "success": False,
            "message": "Please enter a valid email address"
        }), 400

    if len(password) < 8:
        return jsonify({
            "success": False,
            "message": "Password must be at least 8 characters long"
        }), 400

    users = load_users()

    for user in users:

        if user["email"] == email:

            return jsonify({
                "success": False,
                "message": "Email already exists"
            })

    users.append({

        "name": name,
        "email": email,
        "password": generate_password_hash(password),
        "role": role,
        "phone": phone

    })

    save_users(users)

    return jsonify({
        "success": True,
        "message": "Registration Successful"
    })


# ==========================
# Login
# ==========================
@app.route("/login", methods=["POST"])
def login():

    data = request.get_json(silent=True) or {}

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required"
        }), 400

    if is_locked_out(email):
        return jsonify({
            "success": False,
            "message": "Too many failed attempts. Please try again in a few minutes."
        }), 429

    users = load_users()

    for user in users:

        if user["email"] != email:
            continue

        stored_hash = user["password"]

        # Werkzeug hashes are self-describing (method$salt$hash); legacy
        # accounts still hold a bare sha256 hex digest, so fall back and
        # transparently upgrade them once the correct password is proven.
        if "$" in stored_hash or stored_hash.startswith("pbkdf2:") or stored_hash.startswith("scrypt:"):
            valid = check_password_hash(stored_hash, password)
        else:
            valid = stored_hash == hash_password(password)
            if valid:
                user["password"] = generate_password_hash(password)
                save_users(users)

        if valid:
            clear_failed_login(email)
            session["user"] = public_user(user)

            return jsonify({
                "success": True
            })

        break

    register_failed_login(email)

    return jsonify({
        "success": False,
        "message": "Invalid Email or Password"
    })

# ==========================
# Logout
# ==========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

# ==========================
# AI Recommendation
# ==========================

@app.route("/recommend-buyers")
def recommend_buyers():

    if "user" not in session:
        return jsonify({"success": False}), 401

    with open(MANUFACTURERS_FILE) as f:
        manufacturers = json.load(f)

    with open(BUYERS_FILE) as f:
        buyers = json.load(f)


    manufacturer = manufacturers[0]


    prompt = f"""
        You are an AI recommendation engine.

        Manufacturer:
        {json.dumps(manufacturer, indent=4)}

        Buyers:
        {json.dumps(buyers, indent=4)}

        Recommend the best 3 buyers.

        Consider:
        - Product match
        - Location
        - Demand
        - Business compatibility
        - Order requirements

        Return ONLY JSON.
        """


    try:

        response = client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[
                {
                    "role": "system",
                    "content": 
                    "You are an AI recommendation engine. "
                    "Always return valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.2,

            max_tokens=500
        )


        result = response.choices[0].message.content


        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(result)


        return jsonify({
            "status": "live",
            "recommendations": result
        })


    except Exception as e:


        if os.path.exists(CACHE_FILE):

            with open(CACHE_FILE, "r", encoding="utf-8") as f:

                return jsonify({
                    "status": "cached",
                    "recommendations": f.read()
                })


        return jsonify({
            "status": "error",
            "message": str(e)
        })
    
@app.route("/translate", methods=["POST"])
def translate():

    if "user" not in session:
        return jsonify({"success": False}), 401

    data = request.get_json(silent=True) or {}

    text = (data.get("text") or "").strip()
    language = data.get("language")

    if not text or not language:
        return jsonify({
            "status": "error",
            "translated": "Text and target language are required."
        }), 400

    CACHE_FILE = "translation_cache.json"

    prompt = f"""
    You are a professional business translator.

    Translate the following text into {language}.

    Requirements:
    - Preserve the meaning.
    - Use professional business language.
    - Keep product names unchanged if needed.
    - Do not explain anything.

    Return ONLY the translated text.

    Text:
    {text}
    """

    try:

        response = client.chat.completions.create(

            model="llama-3.1-8b-instant",

            messages=[
                {
                    "role": "system",
                    "content": 
                    "You are a professional business translator."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.3,

            max_tokens=300
        )


        translated = response.choices[0].message.content.strip()


        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "translated": translated
                },
                f,
                ensure_ascii=False,
                indent=4
            )


        return jsonify({
            "status": "live",
            "translated": translated
        })


    except Exception as e:


        if os.path.exists(CACHE_FILE):

            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cached = json.load(f)


            return jsonify({
                "status": "cached",
                "translated": cached["translated"]
            })


        return jsonify({
            "status": "error",
            "translated": "Translation unavailable.",
            "error": str(e)
        }), 500

@app.route("/market-demand", methods=["POST"])
def market_demand():

    if "user" not in session:
        return jsonify({"success": False}), 401

    data = request.get_json(silent=True) or {}

    product = data.get("product")
    location = data.get("location")

    if not product or not location:
        return jsonify({
            "status": "error",
            "message": "Product and location are required."
        }), 400

    prompt = f"""
You are an AI market demand analysis engine.

Analyze the market demand for this product.

Product:
{product}

Location:
{location}

Provide:
- Demand level (High/Medium/Low)
- Estimated market opportunity
- Target customers
- Best selling season
- Pricing suggestion
- Growth prediction
- Reasons behind your analysis

Return ONLY JSON.
"""


    try:

        response = client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            response_format={
                "type": "json_object"
            },

            messages=[

                {
                    "role": "system",
                    "content":
                    "You are an expert AI market analyst. "
                    "Return only valid JSON."
                },

                {
                    "role": "user",
                    "content": prompt
                }

            ],

            temperature=0.2,

            max_tokens=700
        )


        result = response.choices[0].message.content


        return jsonify({
            "status": "live",
            "market_analysis": json.loads(result)
        })


    except Exception as e:

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
@app.route("/market-insights")
def market_insights():

    if "user" not in session:
        return jsonify({"success": False}), 401

    user = session["user"]

    prompt = f"""
You are an AI market analyst.

User Role:
{user["role"]}

Generate exactly 3 market insights for Kashmiri handicrafts.

Return ONLY JSON in this format:

{{
    "insights":[
        {{
            "title":"...",
            "trend":"up",
            "percentage":18,
            "reason":"..."
        }}
    ]
}}
"""

    try:

        response = client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            response_format={"type":"json_object"},

            messages=[
                {
                    "role":"system",
                    "content":"Return only valid JSON."
                },
                {
                    "role":"user",
                    "content":prompt
                }
            ],

            temperature=0.3,
            max_tokens=500
        )

        result = json.loads(response.choices[0].message.content)

        return jsonify(result)

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }),500
    
@app.route("/ai-dashboard")
def ai_dashboard():

    if "user" not in session:
        return jsonify({"success": False}), 401

    user = session["user"]

    prompt = f"""
You are Dastkaar AI.

User:
Name: {user["name"]}
Role: {user["role"]}

Generate an AI business dashboard for this manufacturer.

Return ONLY valid JSON.

Use EXACTLY this schema:

{{
    "buyers":[
        {{
            "name":"Buyer Name",
            "country":"Country",
            "type":"Importer",
            "match":95
        }},
        {{
            "name":"Buyer Name",
            "country":"Country",
            "type":"Retailer",
            "match":91
        }},
        {{
            "name":"Buyer Name",
            "country":"Country",
            "type":"Distributor",
            "match":87
        }}
    ],

    "demand":{{
        "months":["Feb","Mar","Apr","May","Jun","Jul"],
        "values":[45,58,63,72,81,93]
    }},

    "products":[
        {{
            "name":"Product Name",
            "category":"Category",
            "price":"$120",
            "match":94
        }},
        {{
            "name":"Product Name",
            "category":"Category",
            "price":"$95",
            "match":89
        }}
    ],

    "quality":{{
        "overall":92,
        "craftsmanship":95,
        "material":91,
        "listing":88
    }},

    "suggestions":[
        "Suggestion 1",
        "Suggestion 2",
        "Suggestion 3"
    ]
}}

Rules:
- Return ONLY JSON.
- Do NOT wrap the JSON in markdown.
- buyers must contain exactly 3 buyers.
- products must contain exactly 2 products.
- suggestions must contain exactly 3 suggestions.
- demand.values must contain exactly 6 integers.
- Every demand value must be between 10 and 100.
"""

    try:

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "Return valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3
        )

        content = response.choices[0].message.content

        print("=" * 60)
        print(content)
        print("=" * 60)

        return jsonify(json.loads(content))

    except Exception as e:

        print(e)

        return jsonify({
            "buyers": [],
            "demand": {
                "months": ["Feb", "Mar", "Apr", "May", "Jun", "Jul"],
                "values": [45, 58, 63, 72, 81, 93]
            },
            "products": [],
            "quality": {
                "overall": 92,
                "craftsmanship": 95,
                "material": 91,
                "listing": 88
            },
            "suggestions": [
                "Unable to generate AI suggestions."
            ]
        })

@app.route("/ai-chat", methods=["POST"])
def ai_chat():

    if "user" not in session:
        return jsonify({
            "success": False,
            "answer": "Please login first."
        }), 401

    data = request.get_json(silent=True) or {}

    question = (data.get("question") or "").strip()

    if not question:
        return jsonify({
            "success": False,
            "answer": "Please enter a question."
        })

    user = session["user"]

    prompt = f"""
You are Dastkaar AI.

You are an AI assistant for a B2B marketplace connecting Kashmiri artisans and manufacturers with global buyers.

Current User

Name: {user["name"]}
Role: {user["role"]}

Answer the user's question professionally.

Keep answers concise (under 200 words).

Question:
{question}
"""

    try:

        response = client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[

                {
                    "role": "system",
                    "content": "You are Dastkaar AI, an expert in exports, handicrafts, pricing, buyers, manufacturing, logistics and international trade."
                },

                {
                    "role": "user",
                    "content": prompt
                }

            ],

            temperature=0.4,
            max_tokens=400

        )

        answer = response.choices[0].message.content

        return jsonify({
            "success": True,
            "answer": answer
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "answer": str(e)
        }), 500
    
@app.route("/market-analytics")
def market_analytics():

    if "user" not in session:
        return jsonify({"success":False}),401

    user=session["user"]
    print(session["user"])

    prompt=f"""
You are an export market analyst.

Manufacturer

Name: {user["name"]}

Business: {user.get("business", "Handicrafts")}

Category: {user.get("role", "Manufacturer")}

Generate ONLY JSON.

{{
    "countries":[
    {{
        "country":"Germany",
        "score":95
    }},
    {{
        "country":"UAE",
        "score":91
    }},
    {{
        "country":"France",
        "score":87
    }}
],
    "products":[
        "Pashmina Shawl",
        "Walnut Furniture",
        "Paper Mache Decor"
    ],

    "price":{{
        "min":120,
        "max":180
    }},

    "months":["Feb","Mar","Apr","May","Jun","Jul"],

    "demand":[45,58,69,73,88,95],

    "tips":[
        "Target premium buyers.",
        "Improve product photography.",
        "Offer bulk discounts."
    ],
    "topMarket":"Germany",
    "priceRange":"$150 - $210",
    "bestMonth":"July",
    "marketTrend":"Growing",

    "countries":[
        {{
        "country":"Germany",
        "score":95
        }},
        {{
        "country":"UAE",
        "score":91
        }},
        {{
        "country":"France",
        "score":87
        }}
    ],

    "products":[
        "Luxury Pashmina Shawls",
        "Walnut Wood Decor",
        "Paper Mache Art"
    ],

    "buyers":[
        {{
        "name":"Nordic Home Co.",
        "country":"Sweden",
        "match":96
        }},
        {{
        "name":"Dubai Craft Imports",
        "country":"UAE",
        "match":93
        }}
    ],

    "price":{{
        "min":120,
        "max":180
    }},

    "months":[
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul"
    ],

    "demand":[45,58,67,74,86,95],

    "tips":[
        "Add professional product photos.",
        "Highlight GI-certified Kashmiri craftsmanship.",
        "Offer wholesale pricing for bulk buyers."
    ],

    "summary":"Demand for premium handcrafted Kashmiri products is rising across Europe and the Middle East."
    }}

"""

    response=client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        response_format={"type":"json_object"},

        messages=[
            {
                "role":"system",
                "content":"Return only valid JSON."
            },
            {
                "role":"user",
                "content":prompt
            }
        ],

        temperature=0.3
    )

    content = response.choices[0].message.content

    print(content)

    return jsonify(json.loads(content))

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")