import telebot
import os, sys
import json
from functools import partial

from tools import photo_by_url, delete_message
from db_tools import create_connection, create, new_users, update_by_id, select_by_id, select_conf_by_id
 
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.Controller import AXISCameraController


########### Data base ###########

data_users = 'db/data_users.db'

create_connection(data_users)
create(data_users)   

#################################



############ Config #############

IO_CONFIG = '/ip-camera/config/io_config.json'
with open(IO_CONFIG, 'r') as fd:
    io_config = json.load(fd)
    
d_zoom = float(io_config['user']['zoom_step'])
d_tilt = float(io_config['user']['tilt_step'])
d_pan = float(io_config['user']['pan_step'])

stream_prefix = str(io_config['connection']['stream_prefix'])
stream_suffix = str(io_config['connection']['stream_suffix'])

ip2url = lambda ip: stream_prefix + ip + stream_suffix
#################################



########### Keyboards ###########

keyboard1 = telebot.types.ReplyKeyboardMarkup(True)
keyboard1.row('zoom in', 'up', 'zoom out')
keyboard1.row('left', 'down', 'right')
keyboard1.row('stop', 'show')

keyboard2 = telebot.types.ReplyKeyboardMarkup()
keyboard2.row('stop')

markup = telebot.types.ReplyKeyboardRemove(selective=False)
#################################



############## Bot ##############

bot = telebot.TeleBot('1434895473:AAGtbUwVgrrJD3QTz3l1Cgh0jh9Rt1Nqjr0')
 
    
@bot.message_handler(commands=['restart'])
def start_handler(message):
    user_id = message.from_user.id
    new_users(user_id, message.from_user.first_name, 0, -1)
    update_by_id(user_id, 'isRunning', 0)
    update_by_id(user_id, 'msg_id', -1)
    bot.send_message(user_id, 'Enter the camera address')


@bot.message_handler(commands=['start', 'go'])
def start_handler(message):
    user_id = message.from_user.id
    new_users(user_id, message.from_user.first_name, 0, -1)
    if not int(select_by_id(user_id, 'isRunning')):
        text = message.text
        msg = bot.send_message(user_id, 'Enter the camera address')
        bot.register_next_step_handler(msg, send_photo)
        update_by_id(user_id, 'isRunning', 1)

        
def send_photo(message):
    try:  
        user_id = message.from_user.id
        text = message.text

        if text == 'stop':
            bot.send_message(user_id, 'stopped', reply_markup=markup)
            update_by_id(user_id, 'isRunning', 0)
            return 

        camera_ip = text
        
        photo = photo_by_url(ip2url(camera_ip))   
        update_by_id(user_id, 'camera_ip', camera_ip)
        
        controller = AXISCameraController(camera_ip)
        isok, conf = controller.get_configuration()
        
        if isok:
            pan, tilt, zoom = conf['pan'], conf['tilt'], conf['zoom']
            update_by_id(user_id, 'pan', pan)
            update_by_id(user_id, 'tilt', tilt)
            update_by_id(user_id, 'zoom', zoom)
        else:
            raise ValueError(ok)
            
        bot.send_photo(user_id, photo, reply_markup=keyboard1)
        msg = bot.send_message(user_id, f'pan={pan},\n tilt={tilt},\n zoom={zoom}')
        update_by_id(user_id, 'msg_id', msg.id)
        bot.register_next_step_handler(msg, partial(move_camera, controller=controller))

    except Exception as e:
        print(e)
        msg = bot.reply_to(message, 'Oooops, invalid address. Try again', reply_markup=keyboard2)
        bot.register_next_step_handler(msg, send_photo)

        
def move_camera(message, controller):
    try:
        user_id = message.from_user.id
        text = message.text
        if text == 'stop':
            bot.send_message(user_id, 'stopped', reply_markup=markup)
            update_by_id(user_id, 'isRunning', 0)
            update_by_id(user_id, 'msg_id', -1)
            return
        elif text == 'show':
            pan, tilt, zoom = select_conf_by_id(user_id)
            
            isok, conf = controller.get_configuration()
            
            if isok:
                conf['pan'] = pan
                conf['tilt'] = tilt
                conf['zoom'] = zoom
                controller.configure(conf)
            else:
                raise ValueError(ok)

            photo = photo_by_url(ip2url(str(select_by_id(user_id, 'camera_ip'))))
            bot.send_photo(user_id, photo, reply_markup=keyboard1)
            
            msg = delete_message(user_id, bot)
            bot.register_next_step_handler(msg, partial(move_camera, controller=controller))
            return
            
        elif text == 'zoom in':
            print(text)
            update_by_id(user_id, 'zoom', min(float(select_by_id(user_id, 'zoom')) + d_zoom, controller.limits[1]['MaxZoom']))
        elif text == 'zoom out': 
            print(text)
            update_by_id(user_id, 'zoom', max(float(select_by_id(user_id, 'zoom')) - d_zoom, controller.limits[1]['MinZoom']))
        elif text == 'right':  
            print(text)
            update_by_id(user_id, 'pan', min(float(select_by_id(user_id, 'pan')) + d_pan, controller.limits[1]['MaxPan']))
        elif text == 'left':  
            print(text)
            update_by_id(user_id, 'pan', max(float(select_by_id(user_id, 'pan')) - d_pan, controller.limits[1]['MinPan']))
        elif text == 'up':  
            print(text)
            update_by_id(user_id, 'tilt', min(float(select_by_id(user_id, 'tilt')) + d_tilt, controller.limits[1]['MaxTilt']))
        elif text == 'down':  
            print(text)
            update_by_id(user_id, 'tilt', max(float(select_by_id(user_id, 'tilt')) - d_tilt, controller.limits[1]['MinTilt']))
        else: 
            bot.send_message(user_id, 'Invalid operation. Try again')
            msg = delete_message(user_id, bot)
            bot.register_next_step_handler(msg, partial(move_camera, controller=controller))
            return
       
        msg = delete_message(user_id, bot)
        bot.register_next_step_handler(msg, partial(move_camera, controller=controller))

    except Exception as e:      
        print(e)
        user_id = message.from_user.id
        bot.clear_step_handler_by_chat_id(user_id)
        bot.reply_to(message, 'Oooops, something went wrong. Try again')
        
        msg = delete_message(user_id, bot)
        bot.register_next_step_handler(msg, partial(move_camera, controller=controller))
        return 

    
bot.polling(none_stop=True)

#################################