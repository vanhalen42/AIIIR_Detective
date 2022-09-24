from getpass import getpass
import yagmail
from telegram.ext.updater import Updater
from telegram import *
from telegram.ext import * 
import shutil
import numpy as np
import os
from os.path import isfile, join
import json
from dotenv import load_dotenv
load_dotenv()
updater = Updater(os.getenv("BOT_TOKEN"),
                  use_context=True)

files_to_send=[join('plots',file,f) for file in os.listdir('plots') for f in os.listdir(join('plots',file))]
recipients=set()

          
            
def send_plot(sensor_name,plot_type,json_file):
    """
    Helper function to send a plot to telegram.
    Args:
        sensor_name: The name of the sensor to send the plot for.
        plot_type: The type of plot to send.
        json_file: The name of the json file containing the telegram chat ids to send the plot to.
    """
    with open(json_file, 'r') as f:
        data = json.load(f)
    dirpath = './output'
    fname = []
    for root,d_names,f_names in os.walk(dirpath):
        for f in f_names:
            fname.append(os.path.join(root, f))
    for file in fname:
        if (sensor_name in file) and (plot_type in file):
            for chat_id in data['registered_chat_ids']:
                try:
                    files_to_send.append(file)
                    updater.bot.send_photo(chat_id=chat_id, photo=open(file, 'rb'),caption = sensor_name+":"+"\n"+""+plot_type+" plot")
                except:
                    print("Error sending document to chat_id: "+str(chat_id))
            

def notify(json_file,markdown_file):
    """
    Helper function to send a text summary to telegram.
    Args:
        json_file: The name of the json file containing the telegram chat ids to send the text to.
        markdown_file: The name of the markdown file containing the text to send.
    """
    with open(json_file, 'r') as f:
        data = json.load(f)
    for chat_id in data['registered_chat_ids']:
        try:
            updater.bot.send_message(chat_id=chat_id, text=markdown_file)
        except:
            print("Error sending document to chat_id: "+str(chat_id))

def send_email(email_text):
    """
    Sends email alerts.
    This function uses the yagmail library to send email alerts. All the unique email addresses for all the folks in charge of different verticals are extracted via verticalconfig.json. The zip, plots, and dead nodes report are then uploaded to the SMTP server as attachments. Subsequently, the email is sent to all the appropriate recipients all at once.
    Args:
        email_text: The text to send in the email.
    """
    pswd=os.getenv('NOTIFIC_SENDER_PASSWORD')
    yag = yagmail.SMTP(os.getenv('NOTIFIC_SENDER_EMAIL'), pswd)
    contents = [
        email_text
    ]
    # contents.extend(f'./{files_to_send}')
    configure_recipients()
    unique_recipients=list(recipients)
    print("Recipients: ")
    for i in range(len(unique_recipients)):  
        print(i+1," : ",unique_recipients[i])
    yag.send(unique_recipients, 'AIIIR Detective Summary', contents,attachments=files_to_send)

def configure_recipients():
    """
    Helper function to configure the unique recipients of the email (to avoid needless redundancy -- what if one person is in charge of multiple verticals?).
    Args:
        email_text: The text to send in the email.
    """
    with open('registered_users.json') as json_file:
        # load config file data
        config_file_data = json.load(json_file)
        # for each vertical in the config file, ...
        for recipient in config_file_data['email_recipients']:
            recipients.add(recipient)
