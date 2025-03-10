import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import json

# تنظیمات توکن و آیدی ادمین
TOKEN = "7942465787:AAE60cConPpMZB9YfGbN7LAr5SRVOk68IyY"
ADMIN_ID = 1149251141
bot = telebot.TeleBot(TOKEN)

# بارگذاری اطلاعات مشتریان و محصولات از فایل JSON
try:
    with open("customers.json", "r") as f:
        customers = json.load(f)
except:
    customers = {}

try:
    with open("products.json", "r") as f:
        products = json.load(f)
except:
    products = {}

# منوی اصلی
main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add(KeyboardButton("📌 ثبت اطلاعات"), KeyboardButton("🛍 محصولات"))
main_menu.add(KeyboardButton("📄 دریافت کاتالوگ"), KeyboardButton("☎ مشاوره"))

# ثبت اطلاعات مشتری
def save_customer(user_id, name, phone, location, job):
    customers[user_id] = {"name": name, "phone": phone, "location": location, "job": job}
    with open("customers.json", "w") as f:
        json.dump(customers, f)

@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.send_message(message.chat.id, "👋 خوش آمدید! لطفاً از منوی زیر انتخاب کنید.", reply_markup=main_menu)

@bot.message_handler(func=lambda message: message.text == "📌 ثبت اطلاعات")
def register_user(message):
    bot.send_message(message.chat.id, "👤 لطفاً نام خود را ارسال کنید.")
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    user_id = message.chat.id
    customers[user_id] = {"name": message.text}
    bot.send_message(message.chat.id, "📞 لطفاً شماره همراه خود را ارسال کنید.")
    bot.register_next_step_handler(message, get_phone)

def get_phone(message):
    user_id = message.chat.id
    customers[user_id]["phone"] = message.text
    bot.send_message(message.chat.id, "📍 لطفاً محدوده فعالیت خود را ارسال کنید.")
    bot.register_next_step_handler(message, get_location)

def get_location(message):
    user_id = message.chat.id
    customers[user_id]["location"] = message.text
    bot.send_message(message.chat.id, "💼 لطفاً عنوان شغلی خود را ارسال کنید.")
    bot.register_next_step_handler(message, get_job)

def get_job(message):
    user_id = message.chat.id
    customers[user_id]["job"] = message.text
    save_customer(user_id, customers[user_id]["name"], customers[user_id]["phone"], customers[user_id]["location"], customers[user_id]["job"])
    bot.send_message(message.chat.id, "✅ اطلاعات شما با موفقیت ثبت شد!", reply_markup=main_menu)

# ارسال کاتالوگ
@bot.message_handler(func=lambda message: message.text == "📄 دریافت کاتالوگ")
def send_catalog(message):
    with open("catalog.pdf", "rb") as catalog:
        bot.send_document(message.chat.id, catalog)

# دریافت مشاوره
@bot.message_handler(func=lambda message: message.text == "☎ مشاوره")
def ask_consultation(message):
    bot.send_message(message.chat.id, "💬 لطفاً سوال خود را ارسال کنید.")
    bot.register_next_step_handler(message, forward_question)

def forward_question(message):
    bot.send_message(ADMIN_ID, f"❓ سوال جدید از {message.chat.id}\n\n📝 سوال: {message.text}\n📞 شماره: {customers.get(message.chat.id, {}).get('phone', 'نامشخص')}")
    bot.send_message(message.chat.id, "✅ سوال شما ثبت شد، به زودی با شما تماس گرفته خواهد شد!", reply_markup=main_menu)

# مدیریت محصولات توسط ادمین
@bot.message_handler(func=lambda message: message.chat.id == ADMIN_ID and message.text == "🛍 مدیریت محصولات")
def manage_products(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("➕ افزودن محصول", callback_data="add_product"))
    markup.add(InlineKeyboardButton("❌ حذف محصول", callback_data="remove_product"))
    bot.send_message(ADMIN_ID, "🔧 مدیریت محصولات:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "add_product")
def add_product(call):
    bot.send_message(ADMIN_ID, "🛒 لطفاً نام محصول را ارسال کنید.")
    bot.register_next_step_handler(call.message, get_product_name)

def get_product_name(message):
    products[message.text] = {"description": "", "video": ""}
    with open("products.json", "w") as f:
        json.dump(products, f)
    bot.send_message(ADMIN_ID, "✅ محصول اضافه شد!")

# نمایش محصولات به مشتریان
@bot.message_handler(func=lambda message: message.text == "🛍 محصولات")
def show_products(message):
    if not products:
        bot.send_message(message.chat.id, "🚫 محصولی یافت نشد!")
        return
    markup = InlineKeyboardMarkup()
    for product in products:
        markup.add(InlineKeyboardButton(product, callback_data=f"product_{product}"))
    bot.send_message(message.chat.id, "📌 لطفاً محصول مورد نظر را انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("product_"))
def show_product_details(call):
    product_name = call.data.replace("product_", "")
    details = products.get(product_name, {})
    bot.send_message(call.message.chat.id, f"🛍 محصول: {product_name}\n📜 توضیحات: {details.get('description', 'ندارد')}\n🎥 ویدیو: {details.get('video', 'ندارد')}")

print("🚀 Bot is running...")
bot.polling(none_stop=True)
