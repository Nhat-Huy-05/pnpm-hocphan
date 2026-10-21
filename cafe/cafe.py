from datetime import datetime
from flask import Flask, render_template, request
from menu import menu_bp

app = Flask(__name__)
app.register_blueprint(menu_bp)

SHOP = {"name":"Cà phê Sông hương", "address": "12 Lê Lợi, Huế", "open": 7, "close": 22}
PROMOTIONS = ["Giảm 10% cho sinh viên",
             "Mua 2 tặng 1 vào thứ Hai"]

@app.get("/")
def index():
    hour = request.args.get("gio",type = int)
    if hour is None:
        hour = datetime.now().hour
    is_open = SHOP["open"] <= hour < SHOP["close"]
    return render_template("index.html", shop=SHOP, promotions=PROMOTIONS, hour=hour, is_open=is_open)


@app.get("/contact")
def contact():
    return render_template("contact.html", shop=SHOP)


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404
