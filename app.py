import os
import json
import traceback

from loguru import logger
from chalice import Chalice
from telegram.ext import (
    CommandHandler,
    Dispatcher,
    MessageHandler,
    Filters,
)
from telegram import Update, Bot

from chalicelib.utils import me, authorize, reply, request_translation_chatgpt

# Telegram token
TOKEN = os.environ["TELEGRAM_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

# Chalice Lambda app
APP_NAME = "translate-gpt-telegram-bot"
MESSAGE_HANDLER_LAMBDA = "translate-gpt-lambda"

app = Chalice(app_name=APP_NAME)
app.debug = True

# Telegram bot
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, use_context=True)


def ask_chatgpt(text):
    try:
        message = request_translation_chatgpt(text)
    except Exception as e:
        logger.error()
        app.log.error(traceback.format_exc())
        return f'Error: {e}'
    else:
        return message

#####################
# Telegram Handlers #
#####################


@authorize
def translate(update, context):
    response = ask_chatgpt(update.message.text)
    reply(response, update.message.chat_id, context)


def ping(update, context):
    chat_id = update.message.chat_id
    user_id = update.to_dict()['message']['from']['id']
    message = f'Version: 1.0\nChatId: {chat_id}\nFromId: {user_id}'
    reply(message, me, context)


def error_handler(update, context):
    logger.warning('ErrorHandler invoked')
    chat_id = update.message.chat_id
    reply(f'Error: {context.error}\n\n{update} ', chat_id, context)


############################
# Lambda Handler functions #
############################

@app.lambda_function(name=MESSAGE_HANDLER_LAMBDA)
def message_handler(event, context):
    dispatcher.add_handler(CommandHandler('ping', ping))
    dispatcher.add_handler(MessageHandler(Filters.text, translate))
    dispatcher.add_error_handler(error_handler)

    try:
        dispatcher.process_update(
            Update.de_json(json.loads(event["body"]), bot))
    except Exception as e:
        print(e)
        return {"statusCode": 500}

    return {"statusCode": 200}
