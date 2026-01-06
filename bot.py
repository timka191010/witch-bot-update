from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# ЗАМЕНИ НА СВОЙ ТОКЕН ОТ @BotFather
TOKEN = "8500508012:AAEMuWXEsZsUfiDiOV50xFw928Tn7VUJRH8"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет кнопку для открытия Mini App"""
    keyboard = [[KeyboardButton(
        "🌙 Открыть Клуб Ведьм",
        web_app=WebAppInfo(url="https://witch-club-miniapp.vercel.app")
    )]]
    
    await update.message.reply_text(
        "✨ Добро пожаловать в Клуб Ведьм!\n\n"
        "Нажми кнопку ниже, чтобы заполнить анкету:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

def main():
    """Запускает бота"""
    app = Application.builder().token(TOKEN).build()
    
    # Команда /start
    app.add_handler(CommandHandler("start", start))
    
    print("✅ Бот запущен!")
    print("Отправь боту команду /start")
    
    # Запуск
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
