from datetime import datetime
from math import ceil

from flask import Blueprint, abort, render_template, request

menu_bp = Blueprint("menu", __name__)
ITEMS_PER_PAGE = 3
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
    raw_page = request.args.get("page", "1")
    try:
        page = int(raw_page)
    except ValueError:
        abort(404)

    pages = ceil(len(MENU) / ITEMS_PER_PAGE)
    if page < 1 or page > pages:
        abort(404)

    hour = request.args.get("gio", type=int)
    if hour is None:
        hour = datetime.now().hour
    is_open = 7 <= hour < 22
    average_price = sum(item["price"] for item in MENU) / len(MENU)
    available_count = sum(item["available"] for item in MENU)
    start = (page - 1) * ITEMS_PER_PAGE
    return render_template(
        "menu.html",
        menu=MENU[start : start + ITEMS_PER_PAGE],
        menu_count=len(MENU),
        page=page,
        pages=pages,
        hour=hour,
        is_open=is_open,
        average_price=average_price,
        available_count=available_count,
    )
