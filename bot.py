import telebot
from telebot import types
import qrcode
from io import BytesIO

# ===== CONFIG =====

API_TOKEN = "8642550842:AAE8EVLyTdqIKVz8RPjWKEyJfpAGk99_2J0"
ADMIN_ID = 8749717831
UPI_ID = "7023673602@ptaxis"

# ==================

bot = telebot.TeleBot(API_TOKEN)

PRICES = {
    "Shein ₹500 Coupon": 500,
    "Shein ₹1000 Coupon": 1000
}


# ===== MAIN MENU =====
def main_menu(chat_id):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn1 = types.KeyboardButton("Buy Vouchers 🛒")
    btn2 = types.KeyboardButton("Recover Vouchers ♻️")

    markup.add(btn1, btn2)

    bot.send_message(
        chat_id,
        "Welcome to Shein Voucher Store\nChoose option:",
        reply_markup=markup
    )


# ===== START =====
@bot.message_handler(commands=['start'])
def start(message):
    main_menu(message.chat.id)


# ===== BUY =====
@bot.message_handler(func=lambda m: m.text == "Buy Vouchers 🛒")
def buy(message):

    markup = types.InlineKeyboardMarkup()

    btn1 = types.InlineKeyboardButton(
        "Shein ₹500 Coupon",
        callback_data="voucher_500"
    )

    btn2 = types.InlineKeyboardButton(
        "Shein ₹1000 Coupon",
        callback_data="voucher_1000"
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


# ===== PROCESS =====
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
            "Verify Payment",
            callback_data=f"verify_{total}"
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


# ===== VERIFY =====
@bot.callback_query_handler(func=lambda call: call.data.startswith("verify"))
def verify(call):

    total = call.data.split("_")[1]

    bot.send_message(call.message.chat.id, "Payment verification started")

    admin_msg = f"""
New Order

User : @{call.from_user.username}
User ID : {call.from_user.id}

Amount : ₹{total}

Reply with coupon code.
"""

    bot.send_message(ADMIN_ID, admin_msg)


# ===== ADMIN REPLY =====
@bot.message_handler(func=lambda m: m.reply_to_message and m.from_user.id == ADMIN_ID)
def send_coupon(message):

    try:

        text = message.reply_to_message.text

        user_id = int(text.split("User ID : ")[1].split("\n")[0])

        coupon = message.text

        bot.send_message(user_id, f"Your Coupon Code:\n\n{coupon}")

        bot.send_message(ADMIN_ID, "Coupon delivered")

    except:

        bot.send_message(ADMIN_ID, "Delivery failed")


# ===== RECOVER =====
@bot.message_handler(func=lambda m: m.text == "Recover Vouchers ♻️")
def recover(message):

    bot.send_message(message.chat.id, "Send order details to admin")

    bot.send_message(
        ADMIN_ID,
        f"Recover request from user {message.from_user.id}"
    )


print("Bot running...")

bot.infinity_polling()
