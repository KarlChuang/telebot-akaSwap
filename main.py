import configparser
import logging
import requests
import json
import random

import telegram
from flask import Flask, request
from telegram.ext import Dispatcher, MessageHandler, Filters

# Load data from config.ini file
config = configparser.ConfigParser()
config.read('config.ini')

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

# Initial Flask app
app = Flask(__name__)

# Initial bot by Telegram access token
bot = telegram.Bot(token=(config['TELEGRAM']['ACCESS_TOKEN']))


@app.route('/hook', methods=['POST'])
def webhook_handler():
    """Set route /hook with POST method will trigger this method."""
    if request.method == "POST":
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        # Update dispatcher process that handler to process this message
        dispatcher.process_update(update)
    return 'ok'


def reply_handler(update, context):
    """Reply message."""
    chat_id = update.message.chat.id
    if ('auction' in update.message.text):
        res_auctions(chat_id)
    elif ('collection' in update.message.text):
        addr = update.message.text.split(' ')[1]
        res_collection(chat_id, addr)
    elif ('creation' in update.message.text):
        addr = update.message.text.split(' ')[1]
        res_creation(chat_id, addr)
    else:
        res_default(chat_id)

def res_default(chat_id):
    try:
        response = requests.get("https://api.akaswap.com/v2/statistics/top-creators", verify=False)
        response = response.json()
        creators = response['topCreators']
        creator = creators[int(random.random() * len(creators))]['creator']
        response = requests.get("https://api.akaswap.com/v2/accounts/%s/creations" % creator, verify=False)
        response = response.json()
        tokens = response['tokens']
        token = tokens[int(random.random() * len(tokens))]
        uri = 'https://ipfs.io/ipfs/%s' % token['thumbnailUri'].split("//")[1]
        caption = "[%s]  (%s xtz)\n%s\n" % (
            token['name'],
            token['recentlySoldPrice'] / 1000000,
            token['description']
        )
        bot.send_photo(chat_id, uri, filename=token['name'], caption=caption)
    except:
        res_default(chat_id)

def res_collection(chat_id, addr):
    response = requests.get(
        "https://api.akaswap.com/v2/accounts/%s/collections?sortBy=soldTime&limit=6"
        % addr,
        verify=False)
    response = response.json()
    # with open('data.json', 'w') as f:
    #     json.dump(response, f)
    tokens = response['tokens']
    medias = []
    for token in tokens:
        uri = 'https://ipfs.io/ipfs/%s' % token['thumbnailUri'].split("//")[1]
        caption = "[%s]  (%s xtz)\n%s\n" % (token['name'],
                                            token['recentlySoldPrice'] / 1000000,
                                            token['description'])
        medias.append(telegram.InputMediaPhoto(media=uri,
                                               filename=token['name'],
                                               caption=caption))
    bot.send_media_group(chat_id, medias)


def res_creation(chat_id, addr):
    response = requests.get(
        "https://api.akaswap.com/v2/accounts/%s/creations?sortBy=mintTime&limit=10"
        % addr,
        verify=False)
    response = response.json()
    # with open('data.json', 'w') as f:
    #     json.dump(response, f)
    tokens = response['tokens']
    medias = []
    for token in tokens:
        uri = 'https://ipfs.io/ipfs/%s' % token['thumbnailUri'].split("//")[1]
        caption = "[%s]  (%s xtz)\n%s\n" % (token['name'],
                                            token['recentlySoldPrice'] / 1000000,
                                            token['description'])
        medias.append(telegram.InputMediaPhoto(media=uri,
                                               filename=token['name'],
                                               caption=caption))
    bot.send_media_group(chat_id, medias)

def res_auctions(chat_id):
    response = requests.get("https://api.akaswap.com/v2/auctions?limit=30", verify=False)
    response = response.json()
    # with open('data.json', 'w') as f:
    #     json.dump(response, f)
    auctions = response['auctions']
    medias = []
    for auction in auctions:
        uri = 'https://ipfs.io/ipfs/%s' % auction['token']['thumbnailUri'].split("//")[1]
        caption = "[%s]  (%s xtz)\n%s\n" % (
            auction['title'],
            auction['currentStorePrice'] / 1000000,
            auction['description']
        )
        medias.append(telegram.InputMediaPhoto(
            media=uri,
            filename=auction['title'],
            caption=caption
        ))
    bot.send_media_group(chat_id, medias)


# New a dispatcher for bot
dispatcher = Dispatcher(bot, None)

# Add handler for handling message, there are many kinds of message. For this handler, it particular handle text
# message.
dispatcher.add_handler(MessageHandler(Filters.text, reply_handler))

if __name__ == "__main__":
    # Running server
    app.run(debug=True)