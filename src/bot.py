from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.filters import Filters
from telegram import *
from telegram.ext import * 
import os
import json
from dotenv import load_dotenv
load_dotenv()
updater = Updater(os.getenv("BOT_TOKEN"),
                  use_context=True)
  
  
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Hi! I'm the AIIIR Detective bot!\n Type /help to get started.")
  
def help(update: Update, context: CallbackContext):
    update.message.reply_text("""Available Commands :-
    /register - register for daily and weekly summary and updates
    /unregister - unregister for daily and weekly summary and updates
    /help - get help""")
  
def register_user(update: Update, context: CallbackContext):
    # open json file
    with open('registered_users.json', 'r') as f:
        registered_users = json.load(f)
    # add user to json file
    if update.effective_chat.id not in registered_users['registered_chat_ids']:
        registered_users['registered_chat_ids'].append(update.effective_chat.id)
        # save json file
        with open('registered_users.json', 'w') as f:
            json.dump(registered_users, f)
        update.message.reply_text("Registered Successfully!")
    else:
        update.message.reply_text("You are already registered!")

def unregister_user(update: Update, context: CallbackContext):
    # open json file
    with open('registered_users.json', 'r') as f:
        registered_users = json.load(f)
    # remove user from json file
    if update.effective_chat.id in registered_users['registered_chat_ids']:
        registered_users['registered_chat_ids'].remove(update.effective_chat.id)
        # save json file
        with open('registered_users.json', 'w') as f:
            json.dump(registered_users, f)
        update.message.reply_text("Unregistered Successfully!")
    else:
        update.message.reply_text("You are not registered!")

# def daily_update(update: Update, context: CallbackContext):
#     with open('verticalconfig.json', 'r') as f:
#         verticalconfig = json.load(f)
#     keyboard_list = []
#     for val in verticalconfig['verticals']:
#         keyboard_list.append(KeyboardButton(val['vertical_id']))
#     buttons = [keyboard_list]
#     context.bot.send_message(chat_id=update.effective_chat.id, text="Click the vertical for more info!", reply_markup=ReplyKeyboardMarkup(buttons))

def unknown(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Sorry '%s' is not a valid command" % update.message.text)
  
  
def unknown_text(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Sorry I can't recognize you , you said '%s'" % update.message.text)
  

updater.dispatcher.add_handler(CommandHandler('help', help))
updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CommandHandler('register', register_user))
updater.dispatcher.add_handler(CommandHandler('unregister', unregister_user))
# updater.dispatcher.add_handler(CommandHandler('dailyupdate', daily_update))
updater.dispatcher.add_handler(MessageHandler(Filters.text, unknown))
updater.dispatcher.add_handler(MessageHandler(
    Filters.command, unknown))  # Filters out unknown commands
  
# Filters out unknown messages.
updater.dispatcher.add_handler(MessageHandler(Filters.text, unknown_text))
updater.start_polling()
