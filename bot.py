import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from flask import Flask, request

# Ваш токен бота
TOKEN = "7203941606:AAFxdSd7TZsTPNV2uSu_sjFjoqAfHStEAlU"
CHANNEL_ID = "@satislegends"  # или числовой ID

# Включаем логирование для отслеживания ошибок
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Этапы разговора
TITLE, DESCRIPTION, PRICE, CONTACT, PHOTO, CONFIRMATION, RESTART = range(7)

# Flask приложение для обработки webhook запросов
app = Flask(__name__)

# Стартовая команд
async def start(update: Update, context: CallbackContext):
    context.user_data.clear()
    await update.message.reply_text('Merhaba! Size bir ilan yayınlamanızda yardımcı olacağım. '
                                    'Lütfen ürünün adını gönderin.')
    return TITLE

# Обработка текста (название товара)
async def get_title(update: Update, context: CallbackContext):
    context.user_data['title'] = update.message.text
    await update.message.reply_text('Harika! Şimdi ürünün açıklamasını gönderin.')
    return DESCRIPTION

# Обработка описания товара
async def get_description(update: Update, context: CallbackContext):
    context.user_data['description'] = update.message.text
    await update.message.reply_text('İyi! Şimdi ürünün fiyatını belirtin.')
    return PRICE

# Обработка цены
async def get_price(update: Update, context: CallbackContext):
    context.user_data['price'] = update.message.text
    await update.message.reply_text('Harika! Şimdi telefon numaranızı veya Telegram bilgilerinizi gönderin.')
    return CONTACT

# Обработка контакта (телефон или Telegram)
async def get_contact(update: Update, context: CallbackContext):
    context.user_data['contact'] = update.message.text
    await update.message.reply_text('Şimdi ürünün fotoğrafını gönderin.')
    return PHOTO

# Обработка фото
async def get_photo(update: Update, context: CallbackContext):
    context.user_data['photo'] = update.message.photo[-1].file_id
    await update.message.reply_text('Harika! İlanınız yayınlamaya hazır. '
                                    'Lütfen onaylayın.')
    await update.message.reply_text('İşte ürününüz:\n'
                                    f"📦 {context.user_data['title']}\n"
                                    f"📝 {context.user_data['description']}\n"
                                    f"💰 {context.user_data['price']}\n"
                                    f"📞 {context.user_data['contact']}")
    await update.message.reply_text('İlanınızı göndermeyi onaylıyor musunuz? "Evet" yazın, her şey doğruysa, '
                                    'ya da "Hayır" yazın, değişiklik yapmak için.')
    return CONFIRMATION

# Подтверждение отправки объявления
async def confirm_ad(update: Update, context: CallbackContext):
    user_response = update.message.text.lower()

    if user_response == 'evet':
        text = f"📦 Yeni ürün:\n" \
               f"{context.user_data['title']}\n" \
               f"📝 {context.user_data['description']}\n" \
               f"💰 {context.user_data['price']}\n" \
               f"📞 {context.user_data['contact']}"

        if 'photo' in context.user_data:
            await context.bot.send_photo(CHANNEL_ID, context.user_data['photo'], caption=text)
        else:
            await context.bot.send_message(CHANNEL_ID, text)

        await update.message.reply_text('İlanınız başarıyla kanala gönderildi!')

        await update.message.reply_text(
            'Başka bir ilan vermek ister misiniz? "Evet" yazın, devam etmek için veya "Hayır" yazın, bitirmek için.')
        return RESTART

    elif user_response == 'hayır':
        await update.message.reply_text('Tamam! Başka bir ilan vermek için lütfen ürünün adını gönderin.')
        return TITLE
    else:
        await update.message.reply_text('Lütfen "Evet" yazın, her şey doğruysa veya "Hayır" yazın, değişiklik yapmak için.')
    return CONFIRMATION

# Спросить пользователя, если он хочет опубликовать еще одно объявление
async def ask_restart(update: Update, context: CallbackContext):
    user_response = update.message.text.lower()

    if user_response == 'evet':
        context.user_data.clear()
        await update.message.reply_text('Tamam, ürünün adını gönderin lütfen.')
        return TITLE

    elif user_response == 'hayır':
        await update.message.reply_text('Botu kullandığınız için teşekkürler! Hoşça kalın!')
        return ConversationHandler.END

    else:
        await update.message.reply_text('Lütfen "Evet" yazın, devam etmek için veya "Hayır" yazın, bitirmek için.')

    return RESTART

# Обработчик ошибок
async def error(update: Update, context: CallbackContext):
    logger.warning(f'Update {update} caused error {context.error}')

# Обработка отмены
async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text('İlan iptal edildi. Başlamak için /start yazın.')
    return ConversationHandler.END

# Flask endpoint для webhook
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_str = request.get_data(as_text=True)
    update = Update.de_json(json_str, application.bot)
    application.process_update(update)
    return 'OK'

def main():
    # Создаем объект Application
    global application
    application = Application.builder().token(TOKEN).build()

    # Обработчики разговоров
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
            PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
            CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_ad)],
            RESTART: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_restart)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conversation_handler)

    # Обработка ошибок
    application.add_error_handler(error)

    # Устанавливаем webhook
    application.bot.set_webhook(url=f'https://your-domain.com/{TOKEN}')

    # Запускаем Flask для обработки входящих запросов
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == '__main__':
    main()
