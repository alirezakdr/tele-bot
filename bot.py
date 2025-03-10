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
# ایجاد جدول محصولات و دستورالعمل‌ها
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
# افزودن محصول جدید توسط ادمین
@bot.message_handler(commands=['add_product'])
def add_product_step1(message):
    if str(message.chat.id) != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ شما دسترسی لازم را ندارید!")
        return

    bot.send_message(message.chat.id, "📦 لطفاً نام محصول را وارد کنید:")
    bot.register_next_step_handler(message, add_product_step2)

def add_product_step2(message):
    product_name = message.text
    bot.send_message(message.chat.id, "📂 لطفاً دسته‌بندی محصول را وارد کنید:")
    bot.register_next_step_handler(message, lambda msg: save_product(msg, product_name))

def save_product(message, product_name):
    category = message.text
    cursor.execute("INSERT INTO products (name, category) VALUES (?, ?)", (product_name, category))
    conn.commit()
    bot.send_message(message.chat.id, f"✅ محصول **{product_name}** با دسته‌بندی **{category}** اضافه شد!")

# افزودن دستورالعمل برای محصول
@bot.message_handler(commands=['add_instruction'])
def add_instruction_step1(message):
    if str(message.chat.id) != ADMIN_ID:
        bot.send_message(message.chat.id, "⛔ شما دسترسی لازم را ندارید!")
        return

    bot.send_message(message.chat.id, "📦 لطفاً نام محصولی که می‌خواهید دستورالعمل آن را ثبت کنید، وارد کنید:")
    bot.register_next_step_handler(message, add_instruction_step2)

def add_instruction_step2(message):
    product_name = message.text
    cursor.execute("SELECT id FROM products WHERE name = ?", (product_name,))
    product = cursor.fetchone()

    if not product:
        bot.send_message(message.chat.id, "❌ این محصول وجود ندارد! ابتدا محصول را ثبت کنید.")
        return

    product_id = product[0]
    bot.send_message(message.chat.id, "📝 لطفاً دستورالعمل متنی را ارسال کنید:")
    bot.register_next_step_handler(message, lambda msg: save_instruction(msg, product_id))

def save_instruction(message, product_id):
    instruction_text = message.text
    cursor.execute("INSERT INTO instructions (product_id, text) VALUES (?, ?)", (product_id, instruction_text))
    conn.commit()
    bot.send_message(message.chat.id, "✅ دستورالعمل با موفقیت ثبت شد! اگر می‌خواهید ویدیو هم اضافه کنید، لینک آن را ارسال کنید.")

    bot.register_next_step_handler(message, lambda msg: save_video(msg, product_id))

def save_video(message, product_id):
    video_url = message.text
    cursor.execute("UPDATE instructions SET video_url = ? WHERE product_id = ?", (video_url, product_id))
    conn.commit()
    bot.send_message(message.chat.id, "🎥 ویدیو نیز اضافه شد!")

@bot.message_handler(commands=['get_instruction'])
def get_instruction_step1(message):
    bot.send_message(message.chat.id, "📦 لطفاً نام محصولی که می‌خواهید دستورالعمل آن را دریافت کنید، وارد کنید:")
    bot.register_next_step_handler(message, get_instruction_step2)

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

from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# تابع برای نمایش منوی اصلی
def show_main_menu(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)

    btn1 = KeyboardButton("📦 محصولات")
    btn2 = KeyboardButton("📖 دریافت دستورالعمل")
    btn3 = KeyboardButton("💬 مشاوره رایگان")
    btn4 = KeyboardButton("📄 دریافت کاتالوگ")
    btn5 = KeyboardButton("ℹ️ درباره ما")

    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5)

    bot.send_message(chat_id, "🏠 **به منوی اصلی خوش آمدید! لطفاً یک گزینه را انتخاب کنید:**", reply_markup=markup, parse_mode="Markdown")

# هندلر برای شروع و نمایش منو
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id

    # بررسی اینکه آیا مشتری قبلاً ثبت شده یا نه
    cursor.execute("SELECT * FROM customers WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        bot.send_message(user_id, "🔹 لطفاً ابتدا اطلاعات خود را وارد کنید.\n✏️ نام و نام خانوادگی:")
        bot.register_next_step_handler(message, get_name)
    else:
        show_main_menu(user_id)


@bot.message_handler(func=lambda message: message.text == "📦 محصولات")
def show_products(message):
    bot.send_message(message.chat.id, "📦 لطفاً نام محصول موردنظر خود را وارد کنید:")
    bot.register_next_step_handler(message, get_instruction_step2)  # از تابع قبلی استفاده می‌کنیم

@bot.message_handler(func=lambda message: message.text == "📖 دریافت دستورالعمل")
def get_instruction(message):
    bot.send_message(message.chat.id, "🔍 لطفاً نام محصول را وارد کنید:")
    bot.register_next_step_handler(message, get_instruction_step2)

@bot.message_handler(func=lambda message: message.text == "💬 مشاوره رایگان")
def consultation(message):
    ask_question(message)

@bot.message_handler(func=lambda message: message.text == "📄 دریافت کاتالوگ")
def send_catalog(message):
    catalog_path = "catalog.pdf"  # مسیر فایل کاتالوگ
    with open(catalog_path, "rb") as catalog:
        bot.send_document(message.chat.id, catalog, caption="📄 کاتالوگ محصولات ما را مشاهده کنید.")

@bot.message_handler(func=lambda message: message.text == "ℹ️ درباره ما")
def about_us(message):
    bot.send_message(message.chat.id, "🏢 **ریمَدی - پیشرو در مراقبت از مو!**\n📌 بیش از ۸ سال تجربه در تولید محصولات کراتین و احیا.\n📞 تماس: +98XXXXXXXXXX\n🌐 وب‌سایت: https://remedy.com", parse_mode="Markdown")

