import telebot
import sqlite3
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# تنظیمات اولیه ربات
TOKEN = "7942465787:AAGsJyyjXL_b6WXI9aQOobOwjqChi4C9GZA"
ADMIN_ID = "1149251141"
bot = telebot.TeleBot(TOKEN)

# اتصال به دیتابیس و ایجاد جدول کاربران
conn = sqlite3.connect("remedy_bot.db", check_same_thread=False)
cursor = conn.cursor()
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
conn.commit()

# شروع ثبت اطلاعات مشتری
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    cursor.execute("SELECT * FROM customers WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    
    if user:
        bot.send_message(user_id, "شما قبلاً ثبت‌نام کرده‌اید!")
    else:
        bot.send_message(user_id, "👋 خوش آمدید! لطفاً نام و نام خانوادگی خود را وارد کنید:")
        bot.register_next_step_handler(message, get_name)

# دریافت نام
def get_name(message):
    user_id = message.chat.id
    name = message.text
    bot.send_message(user_id, "📞 لطفاً شماره همراه خود را وارد کنید:")
    bot.register_next_step_handler(message, get_phone, name)

# دریافت شماره تلفن
def get_phone(message, name):
    user_id = message.chat.id
    phone = message.text
    bot.send_message(user_id, "📍 لطفاً محدوده فعالیت خود را (شهر یا منطقه) وارد کنید:")
    bot.register_next_step_handler(message, get_location, name, phone)

# دریافت محدوده فعالیت
def get_location(message, name, phone):
    user_id = message.chat.id
    location = message.text
    bot.send_message(user_id, "💼 لطفاً عنوان شغلی خود را وارد کنید (مثلاً: آرایشگر، توزیع‌کننده و ...):")
    bot.register_next_step_handler(message, get_job, name, phone, location)

# دریافت عنوان شغلی و ذخیره اطلاعات در دیتابیس
def get_job(message, name, phone, location):
    user_id = message.chat.id
    job = message.text
    cursor.execute("INSERT INTO customers (user_id, name, phone, location, job) VALUES (?, ?, ?, ?, ?)", (user_id, name, phone, location, job))
    conn.commit()
    bot.send_message(user_id, "✅ اطلاعات شما با موفقیت ثبت شد!")
    bot.send_message(ADMIN_ID, f"👤 مشتری جدید ثبت شد:\n📌 نام: {name}\n📞 شماره: {phone}\n📍 محدوده: {location}\n💼 شغل: {job}")

# جستجوی مشتری در بخش ادمین
@bot.message_handler(commands=['search'])
def search_customer(message):
    if str(message.chat.id) != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ شما دسترسی لازم را ندارید!")
        return
    
    bot.send_message(message.chat.id, "🔍 لطفاً نام یا شماره مشتری را وارد کنید:")
    bot.register_next_step_handler(message, find_customer)

# پیدا کردن مشتری
def find_customer(message):
    query = message.text
    cursor.execute("SELECT * FROM customers WHERE name LIKE ? OR phone LIKE ?", (f"%{query}%", f"%{query}%"))
    results = cursor.fetchall()
    
    if results:
        response = "👥 نتایج جستجو:\n"
        for customer in results:
            response += f"\n📌 نام: {customer[2]}\n📞 شماره: {customer[3]}\n📍 محدوده: {customer[4]}\n💼 شغل: {customer[5]}\n---"
        bot.send_message(message.chat.id, response)
    else:
        bot.send_message(message.chat.id, "❌ هیچ مشتری با این اطلاعات یافت نشد!")

# سیستم مشاوره - دریافت سوال از مشتری و ارسال به ادمین
@bot.message_handler(commands=['consult'])
def ask_question(message):
    bot.send_message(message.chat.id, "💬 لطفاً سوال خود را ارسال کنید:")
    bot.register_next_step_handler(message, send_question_to_admin)

def send_question_to_admin(message):
    user_id = message.chat.id
    question = message.text
    cursor.execute("SELECT phone FROM customers WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    phone_number = user_data[0] if user_data else "نامشخص"
    
    bot.send_message(ADMIN_ID, f"📩 سوال جدید از مشتری:\n📞 شماره: {phone_number}\n❓ سوال: {question}")
    bot.send_message(user_id, "✅ سوال شما برای مشاورین ارسال شد. به زودی با شما تماس گرفته خواهد شد.")

# اجرای ربات
bot.polling(none_stop=True)
