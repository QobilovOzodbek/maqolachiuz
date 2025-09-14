import os
from dotenv import load_dotenv
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

load_dotenv()
BOT_TOKEN = os.getenv("bot_token")
API_URL = "http://127.0.0.1:5000"

NAME, SURNAME, PHONE, UNIVERSITY = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.message.from_user.id
    # Serverdan tekshiramiz
    resp = requests.get(f"{API_URL}/user/{tg_id}")
    if resp.status_code == 200 and resp.json().get("registered"):
        await update.message.reply_text(
            "✅ Siz allaqachon ro‘yxatdan o‘tgansiz!\n"
            "Endi maqolangizni yuborishingiz mumkin."
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text("Ismingizni kiriting:")
        return NAME

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["first_name"] = update.message.text
    await update.message.reply_text("Familiyangizni kiriting:")
    return SURNAME

async def surname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["last_name"] = update.message.text
    await update.message.reply_text("Telefon raqamingizni kiriting:")
    return PHONE

async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    await update.message.reply_text("O‘qish joyingizni kiriting:")
    return UNIVERSITY

async def university(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["university"] = update.message.text
    data = {
        "tg_id": update.message.from_user.id,
        "first_name": context.user_data["first_name"],
        "last_name": context.user_data["last_name"],
        "phone": context.user_data["phone"],
        "university": context.user_data["university"],
    }
    resp = requests.post(f"{API_URL}/register", json=data)
    if resp.status_code == 201:
        await update.message.reply_text("✅ Registratsiya yakunlandi!\nMaqolangizni yuboring (PDF shaklida).")
    else:
        await update.message.reply_text("❌ Xatolik yuz berdi, keyinroq urinib ko‘ring.")
    return ConversationHandler.END

import os

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.message.from_user.id

    # 📂 papka mavjudligini tekshirish
    os.makedirs("downloads", exist_ok=True)

    file = await update.message.document.get_file()
    file_path = f"downloads/{tg_id}.pdf"
    await file.download_to_drive(file_path)

    with open(file_path, "rb") as f:
        resp = requests.post(f"{API_URL}/upload_article/{tg_id}", files={"file": f})

    if resp.status_code == 200:
        await update.message.reply_text("✅ Maqolangiz muvaffaqiyatli yuklandi!")
    else:
        await update.message.reply_text("❌ Yuklashda xatolik!")
    
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            SURNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, surname)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone)],
            UNIVERSITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, university)],
        },
        fallbacks=[],
    )

    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))

    app.run_polling()

if __name__ == "__main__":
    main()
