import telebot
import sqlite3
import os
from flask import Flask, request

# تنظیمات توکن و ادمین
TOKEN = os.getenv("7942465787:AAE60cConPpMZB9YfGbN7LAr5SRVOk68IyY")  # گرفتن توکن از محیط متغیرها در Render
ADMIN_ID = os.getenv("1149251141")
bot = telebot.TeleBot(TOKEN)

# تنظیمات Webhook
WEBHOOK_URL = os.getenv("https://tele-bot-c2vq.onrender.com") + "/webhook"

app = Flask(__name__)

# اتصال به دیتابیس
conn = sqlite3.connect("remedy_bot.db", check_same_thread=False)
cursor = conn.cursor()

# ایجاد جداول مورد نیاز در دیتابیس
cursor.execute("""
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    name TEXT,
    phone TEXT,
    location TEXT,
    job TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    category TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS instructions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    text TEXT,
    video_url TEXT,
    FOREIGN KEY (product_id) REFERENCES products (id)
)
""")
conn.commit()

# تابع برای نمایش منوی اصلی
def show_main_menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📦 محصولات", "📖 دریافت دستورالعمل")
    markup.row("💬 مشاوره رایگان", "📄 دریافت کاتالوگ")
    markup.row("ℹ️ درباره ما")
    bot.send_message(chat_id, "🏠 **به منوی اصلی خوش آمدید! لطفاً یک گزینه را انتخاب کنید:**", reply_markup=markup, parse_mode="Markdown")

# ثبت اطلاعات مشتریان
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    cursor.execute("SELECT * FROM customers WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        bot.send_message(user_id, "🔹 لطفاً اطلاعات خود را وارد کنید.\n✏️ نام و نام خانوادگی:")
        bot.register_next_step_handler(message, get_name)
    else:
        show_main_menu(user_id)

def get_name(message):
    name = message.text
    bot.send_message(message.chat.id, "📞 لطفاً شماره تماس خود را وارد کنید:")
    bot.register_next_step_handler(message, lambda msg: save_customer(msg, name))

def save_customer(message, name):
    phone = message.text
    cursor.execute("INSERT INTO customers (user_id, name, phone) VALUES (?, ?, ?)", (message.chat.id, name, phone))
    conn.commit()
    bot.send_message(message.chat.id, "✅ اطلاعات شما ذخیره شد!")
    show_main_menu(message.chat.id)

# پردازش دکمه‌های منو
@bot.message_handler(func=lambda message: message.text == "📦 محصولات")
def show_products(message):
    bot.send_message(message.chat.id, "📦 لطفاً نام محصول موردنظر خود را وارد کنید:")
    bot.register_next_step_handler(message, get_instruction_step2)

@bot.message_handler(func=lambda message: message.text == "📖 دریافت دستورالعمل")
def get_instruction(message):
    bot.send_message(message.chat.id, "🔍 لطفاً نام محصول را وارد کنید:")
    bot.register_next_step_handler(message, get_instruction_step2)

@bot.message_handler(func=lambda message: message.text == "💬 مشاوره رایگان")
def consultation(message):
    bot.send_message(message.chat.id, "💬 لطفاً سوال خود را ارسال کنید:")
    bot.register_next_step_handler(message, send_question_to_admin)

def send_question_to_admin(message):
    user_id = message.chat.id
    question = message.text
    cursor.execute("SELECT phone FROM customers WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    phone_number = user_data[0] if user_data else "نامشخص"
    bot.send_message(ADMIN_ID, f"📩 سوال جدید:\n📞 شماره: {phone_number}\n❓ سوال: {question}")
    bot.send_message(user_id, "✅ سوال شما برای مشاورین ارسال شد.")

@bot.message_handler(func=lambda message: message.text == "📄 دریافت کاتالوگ")
def send_catalog(message):
    with open("catalog.pdf", "rb") as catalog:
        bot.send_document(message.chat.id, catalog, caption="📄 کاتالوگ محصولات ما را مشاهده کنید.")

@bot.message_handler(func=lambda message: message.text == "ℹ️ درباره ما")
def about_us(message):
    bot.send_message(message.chat.id, "🏢 **ریمَدی - پیشرو در مراقبت از مو!**\n📌 بیش از ۸ سال تجربه در تولید محصولات کراتین و احیا.\n📞 تماس: +98XXXXXXXXXX\n🌐 وب‌سایت: https://remedy.com", parse_mode="Markdown")

def get_instruction_step2(message):
    product_name = message.text
    cursor.execute("SELECT i.text, i.video_url FROM instructions i JOIN products p ON i.product_id = p.id WHERE p.name = ?", (product_name,))
    instruction = cursor.fetchone()
    if not instruction:
        bot.send_message(message.chat.id, "❌ برای این محصول هنوز دستورالعمل ثبت نشده است.")
        return
    instruction_text, video_url = instruction
    response = f"📖 دستورالعمل:\n{instruction_text}"
    bot.send_message(message.chat.id, response)
    if video_url:
        bot.send_message(message.chat.id, f"🎥 ویدیوی نمونه‌کار:\n{video_url}")

@app.route("/webhook", methods=["POST"])
def webhook():
    json_data = request.get_json()
    bot.process_new_updates([telebot.types.Update.de_json(json_data)])
    return "", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
