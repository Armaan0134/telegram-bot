import telebot
from telebot import types
import qrcode
from io import BytesIO
from flask import Flask
import threading
import random

# ===== CONFIG =====

API_TOKEN = "8642550842:AAE8EVLyTdqIKVz8RPjWKEyJfpAGk99_2J0"
ADMIN_ID = 8749717831
UPI_ID = "7023673602@ptaxis"

bot = telebot.TeleBot(API_TOKEN)

# ===== FLASK SERVER =====

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host="0.0.0.0", port=10000)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# ===== ORDER + FRAUD PROTECTION =====

approved_orders = set()

def generate_order_id():
    return "ORD" + str(random.randint(100000,999999))

# ===== COUPON SYSTEM =====

def get_coupons(qty):

    with open("coupons.txt","r") as file:
        coupons = file.readlines()

    if len(coupons) < qty:
        return None

    selected = [c.strip() for c in coupons[:qty]]

    with open("coupons.txt","w") as file:
        file.writelines(coupons[qty:])

    return selected

# ===== START =====

@bot.message_handler(commands=['start'])
def start(message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn1 = types.KeyboardButton("Buy Vouchers 🛒")
    btn2 = types.KeyboardButton("Recover Vouchers ♻️")

    markup.add(btn1, btn2)

    bot.send_message(
        message.chat.id,
        "Welcome to Voucher Store\nChoose option:",
        reply_markup=markup
    )

# ===== BUY =====

@bot.message_handler(func=lambda m: m.text == "Buy Vouchers 🛒")
def buy(message):

    markup = types.InlineKeyboardMarkup()

    btn1 = types.InlineKeyboardButton(
        "₹500 Coupon (₹10)",
        callback_data="voucher_10"
    )

    btn2 = types.InlineKeyboardButton(
        "₹1000 Coupon (₹50)",
        callback_data="voucher_50"
    )

    markup.add(btn1)
    markup.add(btn2)

    bot.send_message(message.chat.id,"Choose voucher:",reply_markup=markup)

# ===== SELECT VOUCHER =====

@bot.callback_query_handler(func=lambda call: call.data.startswith("voucher"))
def select(call):

    price = call.data.split("_")[1]

    msg = bot.send_message(call.message.chat.id,"Enter quantity:")

    bot.register_next_step_handler(msg,process_qty,price)

# ===== PROCESS QTY =====

def process_qty(message,price):

    try:

        qty = int(message.text)

        total = int(price) * qty

        order_id = generate_order_id()

        upi_url = f"upi://pay?pa={UPI_ID}&pn=VoucherStore&am={total}&cu=INR&tn=Order-{order_id}"

        qr = qrcode.make(upi_url)

        buf = BytesIO()
        qr.save(buf)
        buf.seek(0)

        caption = f"""
Order ID : {order_id}

Price : ₹{price}
Quantity : {qty}

Total : ₹{total}

Scan QR and pay
"""

        markup = types.InlineKeyboardMarkup()

        btn = types.InlineKeyboardButton(
            "Upload Payment Screenshot",
            callback_data=f"upload_{total}_{order_id}_{qty}"
        )

        markup.add(btn)

        bot.send_photo(
            message.chat.id,
            buf,
            caption=caption,
            reply_markup=markup
        )

    except:

        bot.send_message(message.chat.id,"Send valid quantity number")

# ===== ASK SCREENSHOT =====

@bot.callback_query_handler(func=lambda call: call.data.startswith("upload"))
def ask_screenshot(call):

    data = call.data.split("_")

    amount = data[1]
    order_id = data[2]
    qty = data[3]

    msg = bot.send_message(
        call.message.chat.id,
        "Upload payment screenshot"
    )

    bot.register_next_step_handler(
        msg,
        receive_screenshot,
        amount,
        order_id,
        qty
    )

# ===== RECEIVE SCREENSHOT =====

def receive_screenshot(message,amount,order_id,qty):

    if not message.photo:

        bot.send_message(
            message.chat.id,
            "Please upload screenshot image"
        )

        return

    file_id = message.photo[-1].file_id

    caption = f"""
NEW ORDER

Order ID : {order_id}

User : @{message.from_user.username}
User ID : {message.from_user.id}

Quantity : {qty}
Amount : ₹{amount}
"""

    markup = types.InlineKeyboardMarkup()

    approve = types.InlineKeyboardButton(
        "Approve",
        callback_data=f"approve_{message.from_user.id}_{order_id}_{qty}"
    )

    reject = types.InlineKeyboardButton(
        "Reject",
        callback_data=f"reject_{message.from_user.id}"
    )

    markup.add(approve,reject)

    bot.send_photo(
        ADMIN_ID,
        file_id,
        caption=caption,
        reply_markup=markup
    )

    bot.send_message(
        message.chat.id,
        f"Payment sent for verification\nOrder ID: {order_id}"
    )

# ===== ADMIN APPROVE =====

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve"))
def approve_payment(call):

    data = call.data.split("_")

    user_id = int(data[1])
    order_id = data[2]
    qty = int(data[3])

    if order_id in approved_orders:

        bot.send_message(
            ADMIN_ID,
            "Order already approved"
        )

        return

    approved_orders.add(order_id)

    coupons = get_coupons(qty)

    if coupons is None:

        bot.send_message(
            user_id,
            "Coupon stock finished"
        )

        bot.send_message(
            ADMIN_ID,
            "Not enough coupon stock"
        )

        return

    coupon_text = "\n".join(coupons)

    bot.send_message(
        user_id,
        f"""
Payment Approved ✅

Your Coupon Codes:

{coupon_text}

Thank you for purchase
"""
    )

    bot.send_message(
        ADMIN_ID,
        f"{qty} coupons delivered to {user_id}"
    )

# ===== ADMIN REJECT =====

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject"))
def reject_payment(call):

    user_id = int(call.data.split("_")[1])

    bot.send_message(
        user_id,
        "Payment rejected ❌"
    )

# ===== RECOVER =====

@bot.message_handler(func=lambda m: m.text == "Recover Vouchers ♻️")
def recover(message):

    bot.send_message(
        message.chat.id,
        "Send order ID to admin for recovery"
    )

    bot.send_message(
        ADMIN_ID,
        f"Recover request from {message.from_user.id}"
    )

# ===== START BOT =====

keep_alive()

print("Bot running...")

bot.infinity_polling(none_stop=True)
