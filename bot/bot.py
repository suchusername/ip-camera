import telebot
import cv2
import numpy as np
from PIL import Image
import os, sys

from utools import photo_by_url

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.Controller import AXISCameraController

controller = AXISCameraController("166.145.68.221")

bot = telebot.TeleBot('1434895473:AAGtbUwVgrrJD3QTz3l1Cgh0jh9Rt1Nqjr0')
stream_url = "http://166.145.68.221/mjpg/video.mjpg"
isRunning = False

keyboard1 = telebot.types.ReplyKeyboardMarkup()
keyboard1.row('zoom in', 'up', 'zoom out')
keyboard1.row('left', 'down', 'right')

# the decorator that our bot will use to respond to the /start command.
    
    
@bot.message_handler(commands=['start', 'go'])
def start_handler(message):
    global isRunning
    if not isRunning:
        chat_id = message.chat.id
        text = message.text
        msg = bot.send_message(chat_id, 'Enter the camera address')
        bot.register_next_step_handler(msg, send_photo)
        isRunning = True

        
def send_photo(message):
    chat_id = message.chat.id
    text = message.text
    global stream_url
    stream_url = text
    
    controller.set_default()
    try:
        photo = photo_by_url(stream_url)
    except:
        global isRunning
        isRunning = False
        bot.send_message(chat_id, 'Invalid address')
        return
    
    msg = bot.send_photo(chat_id, photo, reply_markup=keyboard1)
    bot.register_next_step_handler(msg, move_camera)
    
    
def move_camera(message):
    chat_id = message.chat.id
    text = message.text
    if text == 'zoom in':  
        controller.zoom(closer=True)
    elif text == 'zoom out': 
        controller.zoom(closer=False)
    elif text == 'right': 
        controller.pan(right=True)
    elif text == 'left': 
        controller.pan(right=False)
    elif text == 'up': 
        controller.tilt(up=True)
    elif text == 'down': 
        controller.tilt(up=False)
    else:
        global isRunning
        isRunning = False
        bot.send_message(chat_id, 'Invalid operation')
        return
    photo = photo_by_url(stream_url)
    msg = bot.send_photo(chat_id, photo, reply_markup=keyboard1)
    bot.register_next_step_handler(msg, move_camera)

    
    
@bot.message_handler(content_types=['text'])
def send_text(message):
    if message.text == 'Привет':
        bot.send_message(message.chat.id, 'Привет, мой создатель')

bot.polling()