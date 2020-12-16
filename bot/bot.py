import telebot
import cv2
import numpy as np
from PIL import Image

bot = telebot.TeleBot('1434895473:AAGtbUwVgrrJD3QTz3l1Cgh0jh9Rt1Nqjr0')
stream_url = "http://166.145.68.221/mjpg/video.mjpg"


keyboard1 = telebot.types.ReplyKeyboardMarkup(True, True)
keyboard1.row('Привет', 'Пришли фото')

# the decorator that our bot will use to respond to the /start command.
@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет, ты написал мне /start", reply_markup=keyboard1)


@bot.message_handler(content_types=['text'])
def send_text(message):
    if message.text == 'Привет':
        bot.send_message(message.chat.id, 'Привет, мой создатель')
    elif message.text == 'Пришли фото':
        cap = cv2.VideoCapture(stream_url)
        while True:

            ret, frame = cap.read()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#             print(cap.get(cv2.CAP_PROP_POS_FRAMES))
#             print(cap.get(cv2.CAP_PROP_POS_MSEC))

            break
        bot.send_photo(message.chat.id, Image.fromarray(frame))

bot.polling()