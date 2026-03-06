import telebot
from telebot import types
import qrcode
from io import BytesIO
from flask import Flask
import threading

# ===== CONFIG =====

API_TOKEN = "8642550842:AAE8EVLyTdqIKVz8RPjWKEyJfpAGk99_2J0"
ADMIN_ID = 8749717831
UPI_ID = "7023673602@ptaxis"

bot = telebot.TeleBot(API_TOKEN)

# ===== FLASK SERVER (Render Hosting) =====

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host="0.0.0.0", port=10000)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

# ===== COUPON SYSTEM =====

def get_coupon():

    with open("coupons.txt", "r") as file:
        coupons = file.readlines()

    if len(coupons) == 0:
        return None

    coupon = coupons[0].strip()

    with open("coupons.txt", "w") as file:
        file.writelines(coupons[1:])

    return coupon

# ===== PRICES =====

PRICES = {
    "Shein ₹500 Coupon": 99,
    "Shein ₹1000 Coupon": 249
}

# ===== START MENU =====

@bot.message_handler(commands=['start'])
def start(message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn1 = types.KeyboardButton("Buy Vouchers 🛒")
    btn2 = types.KeyboardButton("Recover Vouchers ♻️")

    markup.add(btn1, btn2)

    bot.send_message(
        message.chat.id,
        "Welcome to Shein Voucher Store\nChoose option:",
        reply_markup=markup
    )

# ===== BUY =====

@bot.message_handler(func=lambda m: m.text == "Buy Vouchers 🛒")
def buy(message):

    markup = types.InlineKeyboardMarkup()

    btn1 = types.InlineKeyboardButton(
        "Shein ₹500 Coupon (₹10)",
        callback_data="voucher_10"
    )

    btn2 = types.InlineKeyboardButton(
        "Shein ₹1000 Coupon (₹50)",
        callback_data="voucher_50"
    )

    markup.add(btn1)
    markup.add(btn2)

    bot.send_message(message.chat.id, "Choose voucher:", reply_markup=markup)

# ===== SELECT =====

@bot.callback_query_handler(func=lambda call: call.data.startswith("voucher"))
def select(call):

    amount = call.data.split("_")[1]

    msg = bot.send_message(call.message.chat.id, "Enter quantity:")

    bot.register_next_step_handler(msg, process_qty, amount)

# ===== PROCESS QTY =====

def process_qty(message, amount):

    try:

        qty = int(message.text)

        total = int(amount) * qty

        upi_url = f"upi://pay?pa={UPI_ID}&pn=VoucherStore&am={total}&cu=INR"

        qr = qrcode.make(upi_url)

        buf = BytesIO()
        qr.save(buf)
        buf.seek(0)

        caption = f"""
Order Details

Price : ₹{amount}
Quantity : {qty}

Total : ₹{total}

Scan QR and pay
"""

        markup = types.InlineKeyboardMarkup()

        btn = types.InlineKeyboardButton(
            "Upload Payment Screenshot",
            callback_data=f"upload_{total}"
        )

        markup.add(btn)

        bot.send_photo(
            message.chat.id,
            buf,
            caption=caption,
            reply_markup=markup
        )

    except:

        bot.send_message(message.chat.id, "Send valid number")

# ===== ASK SCREENSHOT =====

@bot.callback_query_handler(func=lambda call: call.data.startswith("upload"))
def ask_screenshot(call):

    amount = call.data.split("_")[1]

    msg = bot.send_message(
        call.message.chat.id,
        "Please upload payment screenshot."
    )

    bot.register_next_step_handler(msg, receive_screenshot, amount)

# ===== RECEIVE SCREENSHOT =====

def receive_screenshot(message, amount):

    if message.photo:

        file_id = message.photo[-1].file_id

        caption = f"""
NEW PAYMENT

User : @{message.from_user.username}
User ID : {message.from_user.id}

Amount : ₹{amount}
"""

        markup = types.InlineKeyboardMarkup()

        approve = types.InlineKeyboardButton(
            "Approve Payment",
            callback_data=f"approve_{message.from_user.id}"
        )

        reject = types.InlineKeyboardButton(
            "Reject Payment",
            callback_data=f"reject_{message.from_user.id}"
        )

        markup.add(approve, reject)

        bot.send_photo(
            ADMIN_ID,
            file_id,
            caption=caption,
            reply_markup=markup
        )

        bot.send_message(
            message.chat.id,
            "Screenshot sent for verification. Please wait."
        )

    else:
        bot.send_message(message.chat.id, "Please send screenshot image.")

# ===== ADMIN APPROVE =====

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve"))
def approve_payment(call):

    user_id = int(call.data.split("_")[1])

    coupon = get_coupon()

    if coupon is None:

        bot.send_message(
            user_id,
            "❌ Coupon stock finished. Contact admin."
        )

        bot.send_message(
            ADMIN_ID,
            "Coupon stock empty."
        )

        return

    bot.send_message(
        user_id,
        f"""
✅ Payment Approved

🎟 Your Coupon Code:

{coupon}

Thank you for purchase.
"""
    )

    bot.send_message(
        ADMIN_ID,
        f"Coupon {coupon} delivered to {user_id}"
    )

# ===== ADMIN REJECT =====

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject"))
def reject_payment(call):

    user_id = int(call.data.split("_")[1])

    bot.send_message(
        user_id,
        "Payment rejected ❌\nContact support."
    )

    bot.send_message(
        ADMIN_ID,
        "Payment rejected."
    )

# ===== RECOVER =====

@bot.message_handler(func=lambda m: m.text == "Recover Vouchers ♻️")
def recover(message):

    bot.send_message(message.chat.id, "Send order details to admin")

    bot.send_message(
        ADMIN_ID,
        f"Recover request from user {message.from_user.id}"
    )

# ===== START BOT =====

keep_alive()

print("Bot running...")

bot.infinity_polling(none_stop=True)
