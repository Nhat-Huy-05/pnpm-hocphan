from datetime import datetime
from flask import Blueprint, render_template, request

menu_bp = Blueprint("menu", __name__)
MENU = [
    {"name": "Cà phê sữa", "price": 20000, "available": True},
    {"name": "Cà phê đen", "price": 15000, "available": True},
    {"name": "Trà sữa", "price": 25000, "available": False},
    {"name": "Sinh tố bơ", "price": 30000, "available": True},
    {"name": "Nước ép cam", "price": 20000, "available": False},
]


@menu_bp.app_template_filter("vnd")
def vnd(value):
    return f"{value:,.0f}".replace(",", ".") + "đ"


@menu_bp.get("/menu")
def menu():
    hour = request.args.get("gio", type=int)
    if hour is None:
        hour = datetime.now().hour
    is_open = 7 <= hour < 22
    average_price = sum(item["price"] for item in MENU) / len(MENU)
    available_count = sum(item["available"] for item in MENU)
    return render_template(
        "menu.html",
        menu=MENU,
        hour=hour,
        is_open=is_open,
        average_price=average_price,
        available_count=available_count,
    )
