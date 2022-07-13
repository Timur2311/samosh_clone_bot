"""
    Telegram event handlers
"""
import sys
import logging
from typing import Dict

import telegram.error
from telegram import Bot, Update, BotCommand, ReplyKeyboardRemove   
from telegram.ext import (
    Updater, Dispatcher, Filters,
    CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, CallbackContext, 
)

from dtb.celery import app  # event processing in async mode
from dtb.settings import TELEGRAM_TOKEN, DEBUG

from tgbot.handlers.utils import files, error
from tgbot.handlers.admin import handlers as admin_handlers
from tgbot.handlers.location import handlers as location_handlers
from tgbot.handlers.onboarding import handlers as onboarding_handlers
from tgbot.handlers.broadcast_message import handlers as broadcast_handlers
from tgbot.handlers.onboarding.manage_data import SECRET_LEVEL_BUTTON
from tgbot.handlers.broadcast_message.manage_data import CONFIRM_DECLINE_BROADCAST
from tgbot.handlers.broadcast_message.static_text import broadcast_command


def setup_dispatcher(dp):
    """
    Adding handlers for events from Telegram
    """
  
    
    ORDER, CART, PLOV, PRODUCT_DETAIL, SALADS, CONTACT_US, FEEDBACK,  = range(7)   
   
        
    
    # onboarding
    # dp.add_handler(CommandHandler("start", onboarding_handlers.command_start))
    
    
    #cart-edit-handler
    dp.add_handler(CallbackQueryHandler(onboarding_handlers.edit_cart_objects, pattern=r"cart-"))
    
    
    
    # admin commands
    # dp.add_handler(CommandHandler("admin", admin_handlers.admin))
    # dp.add_handler(CommandHandler("stats", admin_handlers.stats))
    # dp.add_handler(CommandHandler('export_users', admin_handlers.export_users))

    # location
    # dp.add_handler(CommandHandler("ask_location", location_handlers.ask_for_location))
    # dp.add_handler(MessageHandler(Filters.location, location_handlers.location_handler))

    # # secret level
    # dp.add_handler(CallbackQueryHandler(onboarding_handlers.secret_level, pattern=f"^{SECRET_LEVEL_BUTTON}"))

    # # broadcast message
    # dp.add_handler(
    #     MessageHandler(Filters.regex(rf'^{broadcast_command}(/s)?.*'), broadcast_handlers.broadcast_command_with_message)
    # )
    # dp.add_handler(
    #     CallbackQueryHandler(broadcast_handlers.broadcast_decision_handler, pattern=f"^{CONFIRM_DECLINE_BROADCAST}")
    # )

    # # files
    # dp.add_handler(MessageHandler(
    #     Filters.animation, files.show_file_id,
    # ))

    # handling errors
    dp.add_error_handler(error.send_stacktrace_to_tg_chat)
    
    #Conversation_handler_starts
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', onboarding_handlers.command_start),
            MessageHandler(Filters.text("🛍 Buyurtma berish"), onboarding_handlers.order),
            MessageHandler(Filters.text("☎️ Biz bilan aloqa"), onboarding_handlers.contact_us),
            MessageHandler(Filters.text("✍️ Fikr bildirish"), onboarding_handlers.feedback),
            MessageHandler(Filters.text("Asosiyga qaytish"), onboarding_handlers.back_to_main)
            
            
            ],
        states={
            ORDER: [
                MessageHandler(Filters.text("📥 Savatcha"), onboarding_handlers.cart),             
                MessageHandler(Filters.text('Samarqand Osh'), onboarding_handlers.order_plov),
                MessageHandler(Filters.text('Salatlar'), onboarding_handlers.order_salad),     
                MessageHandler(Filters.text("Asosiyga qaytish"), onboarding_handlers.back_to_main)
                ],
            CART: [
                MessageHandler(Filters.text("Asosiyga qaytish"), onboarding_handlers.back_to_main)                   
                   ],
            
            CONTACT_US: [
                MessageHandler(Filters.text("Asosiyga qaytish"), onboarding_handlers.back_to_main)                   
                   ],
            FEEDBACK: [
                MessageHandler(Filters.text("Asosiyga qaytish"), onboarding_handlers.back_to_main)                   
                   ],
            
            PLOV: [
                MessageHandler(Filters.text("Samarqand Osh Butun"), onboarding_handlers.product_details),
                MessageHandler(Filters.text("Samarqand Osh 0.7"), onboarding_handlers.product_details),
                MessageHandler(Filters.text("⬅️ Ortga"), onboarding_handlers.order)
            ],
             PRODUCT_DETAIL: [
                MessageHandler(Filters.regex("^(1|2|3|4|5|6|7|8|9)$"), onboarding_handlers.count_quantity),
                MessageHandler(Filters.text("⬅️ Ortga"), onboarding_handlers.order)
            ],
            SALADS: [
                MessageHandler(Filters.text("Achchiq-chuchuk"), onboarding_handlers.product_details),
                MessageHandler(Filters.text("Chimcha"), onboarding_handlers.product_details),
                MessageHandler(Filters.text("⬅️ Ortga"), onboarding_handlers.order)
            ],
                 
           
        },
        fallbacks=[],
        allow_reentry =  True
    )

    dp.add_handler(conv_handler)
    
    
    
    

    # EXAMPLES FOR HANDLERS
    # dp.add_handler(MessageHandler(Filters.text, <function_handler>))
    # dp.add_handler(MessageHandler(
    #     Filters.document, <function_handler>,
    # ))
    # dp.add_handler(CallbackQueryHandler(<function_handler>, pattern="^r\d+_\d+"))
    # dp.add_handler(MessageHandler(
    #     Filters.chat(chat_id=int(TELEGRAM_FILESTORAGE_ID)),
    #     # & Filters.forwarded & (Filters.photo | Filters.video | Filters.animation),
    #     <function_handler>,
    # ))

    return dp


def run_pooling():
    """ Run bot in pooling mode """
    updater = Updater(TELEGRAM_TOKEN, use_context=True)

    dp = updater.dispatcher
    dp = setup_dispatcher(dp)

    bot_info = Bot(TELEGRAM_TOKEN).get_me()
    bot_link = f"https://t.me/" + bot_info["username"]

    print(f"Pooling of '{bot_link}' started")
    # it is really useful to send '👋' emoji to developer
    # when you run local test
    # bot.send_message(text='👋', chat_id=<YOUR TELEGRAM ID>)

    updater.start_polling()
    updater.idle()


# Global variable - best way I found to init Telegram bot
bot = Bot(TELEGRAM_TOKEN)
try:
    TELEGRAM_BOT_USERNAME = bot.get_me()["username"]
except telegram.error.Unauthorized:
    logging.error(f"Invalid TELEGRAM_TOKEN.")
    sys.exit(1)


@app.task(ignore_result=True)
def process_telegram_event(update_json):
    update = Update.de_json(update_json, bot)
    dispatcher.process_update(update)


def set_up_commands(bot_instance: Bot) -> None:
    langs_with_commands: Dict[str, Dict[str, str]] = {
        'en': {
            'start': 'Start django bot 🚀',
            'stats': 'Statistics of bot 📊',
            'admin': 'Show admin info ℹ️',
            'ask_location': 'Send location 📍',
            'broadcast': 'Broadcast message 📨',
            'export_users': 'Export users.csv 👥',
        },
        'es': {
            'start': 'Iniciar el bot de django 🚀',
            'stats': 'Estadísticas de bot 📊',
            'admin': 'Mostrar información de administrador ℹ️',
            'ask_location': 'Enviar ubicación 📍',
            'broadcast': 'Mensaje de difusión 📨',
            'export_users': 'Exportar users.csv 👥',
        },
        'fr': {
            'start': 'Démarrer le bot Django 🚀',
            'stats': 'Statistiques du bot 📊',
            'admin': "Afficher les informations d'administrateur ℹ️",
            'ask_location': 'Envoyer emplacement 📍',
            'broadcast': 'Message de diffusion 📨',
            "export_users": 'Exporter users.csv 👥',
        },
        'ru': {
            'start': 'Запустить django бота 🚀',
            'stats': 'Статистика бота 📊',
            'admin': 'Показать информацию для админов ℹ️',
            'broadcast': 'Отправить сообщение 📨',
            'ask_location': 'Отправить локацию 📍',
            'export_users': 'Экспорт users.csv 👥',
        }
    }

    bot_instance.delete_my_commands()
    for language_code in langs_with_commands:
        bot_instance.set_my_commands(
            language_code=language_code,
            commands=[
                BotCommand(command, description) for command, description in langs_with_commands[language_code].items()
            ]
        )


# WARNING: it's better to comment the line below in DEBUG mode.
# Likely, you'll get a flood limit control error, when restarting bot too often
set_up_commands(bot)

n_workers = 0 if DEBUG else 4
dispatcher = setup_dispatcher(Dispatcher(bot, update_queue=None, workers=n_workers, use_context=True))
