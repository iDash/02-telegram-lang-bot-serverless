import openai
import re

from functools import wraps
from loguru import logger
from telegram import ChatAction, ParseMode

me = 0  # me

allowed_ids = []


def reply(text, chat_id, context):
    context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
    )


def is_link(text):
    # Use regular expressions to search for URLs
    url_regex = re.compile(r'^https?://\S+$')
    match = url_regex.match(text)
    return bool(match)


def authorize(func):
    """
    Decorator function to send typing action to chat and check authorization.

    Parameters:
    func (function): the function to be decorated

    Returns:
    function: decorated function with typing action and authorization checks
    """
    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        chat_id = update.effective_message.chat_id
        text = update.message.text.strip()

        if is_link(text) or text.startswith('/'):
            return None
        # if update.message.from_user.is_bot:
        # else:
        #     reply(f'{update.message}', me, context)
        #     reply(f'{update.effective_message}', me, context)
        #     reply(f'{update.message.from_user}', me, context)
        # Check if chat_id is allowed to run the command
        if chat_id in allowed_ids:
            # Send typing action to show the bot is processing
            context.bot.send_chat_action(
                chat_id=chat_id, action=ChatAction.TYPING)
            # Call the command function
            return func(update, context, *args, **kwargs)
        else:
            # Notify admin about unauthorized request
            reply(f'Unauthorized request from {chat_id}', me, context)
            logger.warning(f'Unauthorized request from {chat_id}')
            return None

    return command_func


def request_translation_chatgpt(text):
    logger.info(text)
    prefix = "Translate from Russian into English or from English into Russian: "

    message = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        temperature=0.2,
        max_tokens=250,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,

        messages=[
            # {"role": "system", "content": ". Else FromTranslate from RU to EN or EN to RU, and print only result."},
            {"role": "user", "content": prefix+text}
        ],
    )
    # logger.info(message)
    return message["choices"][0]["message"]["content"]
