import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import os
import json

TOKEN = "7942465787:AAE60cConPpMZB9YfGbN7LAr5SRVOk68IyY"
ADMIN_ID = 1149251141
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your-render-url/webhook")

bot = telebot.TeleBot(TOKEN)

# Load or initialize customer data
def load_data():
    if not os.path.exists("customers.json"):
        with open("customers.json", "w") as f:
            json.dump({}, f)
    with open("customers.json", "r") as f:
        return json.load(f)

def save_data(data):
    with open("customers.json", "w") as f:
        json.dump(data, f)

data = load_data()

# Load or initialize product data
def load_products():
    if not os.path.exists("products.json"):
        with open("products.json", "w") as f:
            json.dump({}, f)
    with open("products.json", "r") as f:
        return json.load(f)

def save_products(products):
    with open("products.json", "w") as f:
        json.dump(products, f)

products = load_products()

# Main menu
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        KeyboardButton("📋 ثبت نام مشتری"),
        KeyboardButton("📞 مشاوره"),
        KeyboardButton("📂 کاتالوگ"),
        KeyboardButton("🛍 محصولات"),
        KeyboardButton("📅 برنامه‌های آینده")
    ]
    markup.add(*buttons)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "👋 خوش آمدید! لطفاً از منوی زیر استفاده کنید.", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "📋 ثبت نام مشتری")
def register_customer(message):
    bot.send_message(message.chat.id, "لطفاً نام خود را وارد کنید:")
    bot.register_next_step_handler(message, process_name)

def process_name(message):
    user_id = message.chat.id
    data[user_id] = {"name": message.text}
    bot.send_message(message.chat.id, "شماره تلفن خود را وارد کنید:")
    bot.register_next_step_handler(message, process_phone)

def process_phone(message):
    user_id = message.chat.id
    data[user_id]["phone"] = message.text
    bot.send_message(message.chat.id, "محدوده فعالیت خود را وارد کنید:")
    bot.register_next_step_handler(message, process_location)

def process_location(message):
    user_id = message.chat.id
    data[user_id]["location"] = message.text
    bot.send_message(message.chat.id, "عنوان شغلی خود را وارد کنید:")
    bot.register_next_step_handler(message, process_job)

def process_job(message):
    user_id = message.chat.id
    data[user_id]["job_title"] = message.text
    save_data(data)
    bot.send_message(message.chat.id, "✅ ثبت نام شما انجام شد!", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "📞 مشاوره")
def consultation(message):
    bot.send_message(message.chat.id, "لطفاً سوال خود را ارسال کنید:")
    bot.register_next_step_handler(message, forward_question)

def forward_question(message):
    bot.send_message(ADMIN_ID, f"📩 سوال جدید از {message.chat.id}\n\n❓ {message.text}")
    bot.send_message(message.chat.id, "✅ سوال شما ارسال شد، به زودی پاسخ داده خواهد شد.")

@bot.message_handler(func=lambda message: message.text == "📂 کاتالوگ")
def send_catalog(message):
    with open("catalog.pdf", "rb") as catalog:
        bot.send_document(message.chat.id, catalog)

@bot.message_handler(func=lambda message: message.text == "🛍 محصولات")
def product_menu(message):
    markup = InlineKeyboardMarkup()
    for product_name in products.keys():
        markup.add(InlineKeyboardButton(product_name, callback_data=f"product_{product_name}"))
    bot.send_message(message.chat.id, "🔹 لطفاً یک محصول را انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("product_"))
def send_product_info(call):
    product_name = call.data.replace("product_", "")
    product_info = products.get(product_name, "اطلاعاتی موجود نیست.")
    bot.send_message(call.message.chat.id, f"🛍 {product_name}\n\n{product_info}")

@bot.message_handler(func=lambda message: message.text == "📅 برنامه‌های آینده")
def upcoming_events(message):
    bot.send_message(message.chat.id, "📅 برنامه‌های آینده به زودی اعلام خواهد شد!")

if __name__ == "__main__":
    import flask
    app = flask.Flask(__name__)

    @app.route(f"/webhook", methods=["POST"])
    def webhook():
        json_str = flask.request.get_data().decode("UTF-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "", 200

    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=5000)
