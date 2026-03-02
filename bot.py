import telebot
from telebot import types
import qrcode
from io import BytesIO
import os

# ================== CONFIG (Render Environment Variables) ==================
API_TOKEN = os.environ.get("8642550842:AAHKWKmDs2jrV8t3xBIoD2BK6cOYTV_Tmro")
ADMIN_ID = int(os.environ.get("8749717831"))
UPI_ID = os.environ.get("7023673602@ptaxis")
# ===========================================================================

bot = telebot.TeleBot(API_TOKEN)

PRICES = {
    "Shein ₹500 Coupon": 500,
    "Shein ₹1000 Coupon": 1000
}

# ================== MAIN MENU ==================

def main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("Buy Vouchers")
    btn2 = types.KeyboardButton("Recover Vouchers")
    markup.add(btn1, btn2)

    bot.send_message(chat_id, "Main Menu 👇", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
    main_menu(message.chat.id)

# ================== BUY VOUCHERS ==================

@bot.message_handler(func=lambda m: m.text == "Buy Vouchers")
def buy_vouchers(message):
    markup = types.InlineKeyboardMarkup()
    for item in PRICES.keys():
        markup.add(types.InlineKeyboardButton(item, callback_data=item))

    bot.send_message(
        message.chat.id,
        "Konsa voucher chahiye? Choose karein:",
        reply_markup=markup
    )

# ================== RECOVER ==================

@bot.message_handler(func=lambda m: m.text == "Recover Vouchers")
def recover(message):
    bot.send_message(message.chat.id, "Apna Order ID bhejein recovery ke liye.")

# ================== ASK QUANTITY ==================

@bot.callback_query_handler(func=lambda call: call.data in PRICES.keys())
def ask_quantity(call):
    bot.answer_callback_query(call.id)

    voucher = call.data
    msg = bot.send_message(
        call.message.chat.id,
        f"Aapne '{voucher}' select kiya hai.\nKitni Quantity chahiye? (Sirf number likhein)"
    )

    bot.register_next_step_handler(msg, generate_qr, voucher)

# ================== GENERATE QR ==================

def generate_qr(message, voucher):
    text = message.text.strip()

    if not text.isdigit():
        bot.send_message(message.chat.id, "Galat input! Sirf number dalein.")
        return

    qty = int(text)

    if qty <= 0:
        bot.send_message(message.chat.id, "Quantity 1 ya usse zyada honi chahiye.")
        return

    total = qty * PRICES[voucher]

    upi_url = f"upi://pay?pa={UPI_ID}&pn=SheinStore&am={total}&cu=INR"

    qr = qrcode.make(upi_url)
    buf = BytesIO()
    qr.save(buf)
    buf.seek(0)

    caption = (
        f"Order Details\n\n"
        f"Item: {voucher}\n"
        f"Quantity: {qty}\n"
        f"Total: Rs {total}\n\n"
        f"QR scan karke payment karein.\n"
        f"Payment ke baad Verify Payment dabayein."
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            "Verify Payment",
            callback_data=f"verify|{voucher}|{qty}|{total}"
        )
    )

    bot.send_photo(
        message.chat.id,
        buf,
        caption=caption,
        reply_markup=markup
    )

# ================== VERIFY PAYMENT ==================

@bot.callback_query_handler(func=lambda call: call.data.startswith("verify"))
def verify_payment(call):
    bot.answer_callback_query(call.id)

    data = call.data.split("|")
    voucher = data[1]
    qty = data[2]
    total = data[3]

    bot.send_message(call.message.chat.id, "Payment verify ho rahi hai... 1-2 minute wait karein.")

    admin_msg = (
        f"Naya Order!\n\n"
        f"User ID: {call.from_user.id}\n"
        f"Username: @{call.from_user.username}\n"
        f"Voucher: {voucher}\n"
        f"Qty: {qty}\n"
        f"Amount: Rs {total}\n\n"
        f"Is message par reply karke coupon bhejein."
    )

    bot.send_message(ADMIN_ID, admin_msg)

# ================== ADMIN REPLY ==================

@bot.message_handler(func=lambda m: m.reply_to_message and m.from_user.id == ADMIN_ID)
def deliver_coupon(message):
    try:
        original_text = message.reply_to_message.text
        user_id = original_text.split("User ID: ")[1].split("\n")[0]

        coupon = message.text

        bot.send_message(
            int(user_id),
            f"Aapka Coupon Code:\n{coupon}\n\nDhanyawad shopping ke liye!"
        )

        bot.send_message(ADMIN_ID, "Coupon successfully bhej diya gaya.")

    except:
        bot.send_message(ADMIN_ID, "Delivery fail! Sahi message par reply karein.")

# ================== RUN ==================

print("Bot is running...")
bot.infinity_polling()
