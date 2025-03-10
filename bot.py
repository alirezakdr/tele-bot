import os
import telebot
from flask import Flask, request

# --- متغیرهای اصلی ---
BOT_TOKEN = "7942465787:AAE60cConPpMZB9YfGbN7LAr5SRVOk68IyY"
ADMIN_ID = 1149251141  # آیدی ادمین تلگرام
RENDER_URL = os.getenv("RENDER_URL", "https://tele-bot-c2vq.onrender.com")  # مقدار پیش‌فرض

# تنظیم وب‌هوک
WEBHOOK_URL = f"{RENDER_URL}/webhook"
print(f"Webhook URL: {WEBHOOK_URL}")

# راه‌اندازی ربات تلگرام
bot = telebot.TeleBot(BOT_TOKEN)

# ایجاد اپلیکیشن Flask
app = Flask(__name__)

# تنظیم مسیر Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_update = request.get_json()
        bot.process_new_updates([telebot.types.Update.de_json(json_update)])
        return "", 200
    else:
        return "Invalid request", 403

# --- دستورات ربات ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "👋 به ربات ریمَدی خوش آمدید! لطفاً از منوی زیر گزینه موردنظر خود را انتخاب کنید.")

# ثبت اطلاعات کاربر
@bot.message_handler(commands=['register'])
def register_user(message):
    bot.send_message(message.chat.id, "✍️ لطفاً نام، شماره تماس و عنوان شغلی خود را وارد کنید.")

# دریافت سوال از کاربر و ارسال به ادمین
@bot.message_handler(commands=['consult'])
def consult_user(message):
    bot.send_message(message.chat.id, "❓ سوال خود را وارد کنید، تیم ما با شما تماس خواهند گرفت.")

# ارسال کاتالوگ به کاربر
@bot.message_handler(commands=['catalog'])
def send_catalog(message):
    with open("catalog.pdf", "rb") as catalog:
        bot.send_document(message.chat.id, catalog)

# --- اجرای ربات ---
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=5000)
