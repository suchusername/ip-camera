import telebot
import os, sys

from tools import photo_by_url, new_users, update_by_id, select_by_id

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.Controller import AXISCameraController

controller = AXISCameraController("166.145.68.221")


########### Data base ###########
data_users = 'data_users.db'
#################################


########### Keyboards ###########
keyboard1 = telebot.types.ReplyKeyboardMarkup(True)
keyboard1.row('zoom in', 'up', 'zoom out')
keyboard1.row('left', 'down', 'right')
keyboard1.row('stop')

keyboard2 = telebot.types.ReplyKeyboardMarkup()
keyboard2.row('stop')

markup = telebot.types.ReplyKeyboardRemove(selective=False)
#################################


############## Bot ##############
bot = telebot.TeleBot('1434895473:AAGtbUwVgrrJD3QTz3l1Cgh0jh9Rt1Nqjr0')
# bot = telebot.AsyncTeleBot("1434895473:AAGtbUwVgrrJD3QTz3l1Cgh0jh9Rt1Nqjr0")
# The decorator that our bot will use to respond to the /start command.
@bot.message_handler(commands=['restart'])
def start_handler(message):
    user_id = message.from_user.id
    new_users(user_id, message.from_user.first_name, '', 0)
    update_by_id(user_id, 'isRunning', 0)
    update_by_id(user_id, 'stream_url', '')
    bot.send_message(user_id, 'Enter the camera address')


@bot.message_handler(commands=['start', 'go'])
def start_handler(message):
    user_id = message.from_user.id
    new_users(user_id, message.from_user.first_name, '', 0)
    if not int(select_by_id(user_id, 'isRunning')):
        text = message.text
        msg = bot.send_message(user_id, 'Enter the camera address')
        bot.register_next_step_handler(msg, send_photo)
        update_by_id(user_id, 'isRunning', 1)


# @bot.message_handler(content_types=['text'])
# def send_text(message):
#     user_id = message.from_user.id
#     new_users(user_id, message.from_user.first_name, '', 0)
#     if message.text == 'Привет':
#         bot.send_message(message.chat.id, 'Привет, мой создатель')
#     if message.text.lower() == 'stop':
#         print('stop1')
#         bot.send_message(user_id, 'stopped', reply_markup=markup)
#         update_by_id(user_id, 'isRunning', 0)        

        
def send_photo(message):
    try:  
        user_id = message.from_user.id
        text = message.text

        if text == 'stop':
            bot.send_message(user_id, 'stopped', reply_markup=markup)
            update_by_id(user_id, 'isRunning', 0)
            return 

        stream_url = text
        update_by_id(user_id, 'stream_url', stream_url)

        controller.set_default()
        photo = photo_by_url(stream_url)   
        
        msg = bot.send_photo(user_id, photo, reply_markup=keyboard1)
        bot.register_next_step_handler(msg, move_camera)

    except Exception as e:
        print(e)
        msg = bot.reply_to(message, 'Oooops, invalid address. Try again', reply_markup=keyboard2)
        bot.register_next_step_handler(msg, send_photo)

    
    
def move_camera(message):
    try:
        user_id = message.from_user.id
        text = message.text
        if text == 'stop':
            bot.send_message(user_id, 'stopped', reply_markup=markup)
            update_by_id(user_id, 'isRunning', 0)
            return         
        elif text == 'zoom in':
            print(text)
            controller.zoom(closer=True)
        elif text == 'zoom out': 
            print(text)
            controller.zoom(closer=False)
        elif text == 'right':  
            print(text)
            controller.pan(right=True)
        elif text == 'left':  
            print(text)
            controller.pan(right=False)
        elif text == 'up':  
            print(text)
            controller.tilt(up=True)
        elif text == 'down':  
            print(text)
            controller.tilt(up=False)
        else: 
#             bot.clear_step_handler_by_chat_id(user_id)
            msg = bot.send_message(user_id, 'Invalid operation. Try again')
            bot.register_next_step_handler(msg, move_camera)
            return
        bot.register_next_step_handler_by_chat_id(user_id, move_camera)
        print('The photo will now start uploading')
        photo = photo_by_url(str(select_by_id(user_id, 'stream_url')))
        msg = bot.send_photo(user_id, photo, reply_markup=keyboard1)
#         bot.register_next_step_handler(msg, move_camera)
        print('Test')
        
    except Exception as e:      
        print(e)
        user_id = message.from_user.id
        bot.clear_step_handler_by_chat_id(user_id)
        msg = bot.reply_to(message, 'Oooops, something went wrong. Try again')
        bot.register_next_step_handler(msg, move_camera)
        return 


bot.polling(none_stop=True)
#################################