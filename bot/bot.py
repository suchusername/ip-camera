import telebot
import os, sys
import json
import requests
import sqlite3
import time
import re
import numpy as np
from functools import partial
from threading import Thread

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tracking import get_frame
from tools import photo_by_url, delete_message, send_by_email
from db_tools import (
    create_connection,
    create,
    new_users,
    update_by_id,
    select_by_id,
    select_conf_by_id,
)

from core.Controller import AXISCameraController
from core.utils import check_ip
import cv2

from yolov3.yolo_wrapper import YOLOv3Wrapper
from yolov3.draw_bboxes import draw_bboxes

from PIL import Image

########### Data base ###########

data_users = "/ip-camera/bot/db/data_users.db"

create_connection(data_users)
create(data_users)

#################################


############ Config #############

IO_CONFIG = "/ip-camera/config/io_config.json"
with open(IO_CONFIG, "r") as fd:
    io_config = json.load(fd)

d_zoom = float(io_config["user"]["zoom_step"])
d_tilt = float(io_config["user"]["tilt_step"])
d_pan = float(io_config["user"]["pan_step"])

stream_prefix = str(io_config["connection"]["stream_prefix"])
stream_suffix = str(io_config["connection"]["stream_suffix"])

ip2url = lambda ip: stream_prefix + ip + stream_suffix
#################################


########### Keyboards ###########

keyboard1 = telebot.types.ReplyKeyboardMarkup(True)
keyboard1.row("zoom in", "up", "zoom out")
keyboard1.row("left", "down", "right")
keyboard1.row("preset", "track")
keyboard1.row("stop", "show")

keyboard2 = telebot.types.ReplyKeyboardMarkup(True, one_time_keyboard=True)
keyboard2.row("stop")

keyboard3 = telebot.types.ReplyKeyboardMarkup(True)
keyboard3.row("stop", "show")


keyboard4 = telebot.types.ReplyKeyboardMarkup(True, one_time_keyboard=True)
keyboard4.row("skip", "stop")

markup = telebot.types.ReplyKeyboardRemove(selective=False)

#################################


############## Model ############

model = YOLOv3Wrapper()
isTracking = False
vehicles = [1, 2, 3, 5, 6]
people = [0]

#################################


############# Email #############

regex = "^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$"

#################################


############## Bot ##############

bot = telebot.TeleBot("1434895473:AAGtbUwVgrrJD3QTz3l1Cgh0jh9Rt1Nqjr0")


@bot.message_handler(commands=["restart"])
def start_handler(message):
    user_id = message.from_user.id
    new_users(user_id, message.from_user.first_name, 0, -1)
    update_by_id(user_id, "isRunning", 0)
    update_by_id(user_id, "msg_id", -1)
    bot.send_message(user_id, "Rebooted")


@bot.message_handler(commands=["help"])
def start_handler(message):
    try:
        user_id = message.from_user.id
        new_users(user_id, message.from_user.first_name, 0, -1)
        bot.send_message(
            user_id,
            " How to use the bot: \n\n1. Type /start \n2. Enter IP address of the camera (Ex: 166.145.68.221) \n3. If connection is successful, you will see a control panel. \n3. To go to a predefined preset, type preset <name>. Empty name corresponds to a default preset.\n",
        )
    except sqlite3.IntegrityError as e:
        return


@bot.message_handler(commands=["start", "go"])
def start_handler(message):
    try:
        user_id = message.from_user.id
        new_users(user_id, message.from_user.first_name, 0, -1)
        if not int(select_by_id(user_id, "isRunning")):
            update_by_id(user_id, "isRunning", 1)
            update_by_id(user_id, "email", "NULL")

            msg = bot.send_message(
                user_id,
                "Enter your email address to receive notifications",
                reply_markup=keyboard4,
            )
            bot.register_next_step_handler(msg, get_email)
    except sqlite3.IntegrityError as e:
        return


def get_email(message):
    try:
        user_id = message.from_user.id
        text = message.text.lower()

        if text == "stop":
            bot.send_message(user_id, "stopped", reply_markup=markup)
            update_by_id(user_id, "isRunning", 0)
            return
        elif text == "skip":
            ...
        elif re.match(regex, text):
            send_by_email(text, "Test email from @incredible_ip_camera_bot")
            update_by_id(user_id, "email", text)
        else:
            raise ValueError("Invalid address")

        msg = bot.send_message(user_id, "Enter the camera ip address")
        bot.register_next_step_handler(msg, get_address)

    except cv2.error as e:
        msg = bot.reply_to(
            message,
            "Failed to upload photo\nTry again or send stop",
            reply_markup=keyboard4,
        )
        bot.register_next_step_handler(msg, get_email)

    except requests.exceptions.ConnectionError as e:
        msg = bot.reply_to(
            message,
            "Connection reset by peer\nTry again or send stop",
            reply_markup=keyboard4,
        )
        bot.register_next_step_handler(msg, get_email)

    except Exception as e:
        print(e)
        msg = bot.reply_to(
            message, f"{e}\nTry again or send stop", reply_markup=keyboard4
        )
        bot.register_next_step_handler(msg, get_email)


def get_address(message):
    try:
        user_id = message.from_user.id
        text = message.text

        if text == "stop":
            bot.send_message(user_id, "stopped", reply_markup=markup)
            update_by_id(user_id, "isRunning", 0)
            return

        camera_ip = text
        if not check_ip(camera_ip):
            raise ValueError("Invalid address")

        photo = photo_by_url(ip2url(camera_ip))

        update_by_id(user_id, "camera_ip", camera_ip)

        controller = AXISCameraController(camera_ip)
        isok, conf = controller.get_configuration()

        if not isok:
            raise ValueError(conf)

        pan, tilt, zoom = conf["pan"], conf["tilt"], conf["zoom"]
        update_by_id(user_id, "pan", round(pan, 1))
        update_by_id(user_id, "tilt", round(tilt, 1))
        update_by_id(user_id, "zoom", round(zoom, 1))

        bot.send_photo(user_id, photo, reply_markup=keyboard1)
        msg = bot.send_message(user_id, f"pan={pan},\ntilt={tilt},\nzoom={zoom}")
        update_by_id(user_id, "msg_id", msg.id)
        bot.register_next_step_handler(msg, partial(move_camera, controller=controller))

    except cv2.error as e:
        msg = bot.reply_to(
            message,
            "Failed to upload photo\nTry again or send stop",
            reply_markup=keyboard2,
        )
        bot.register_next_step_handler(msg, get_address)

    except requests.exceptions.ConnectionError as e:
        msg = bot.reply_to(
            message,
            "Connection reset by peer\nTry again or send stop",
            reply_markup=keyboard2,
        )
        bot.register_next_step_handler(msg, get_address)

    except Exception as e:
        print(e)
        msg = bot.reply_to(
            message, f"{e}\nTry again or send stop", reply_markup=keyboard2
        )
        bot.register_next_step_handler(msg, get_address)


def track_loop(user_id, controller):
    global model
    while select_by_id(user_id, "isTracking"):
        try:
            email = select_by_id(user_id, "email")
            neet_email = not (email == "NULL")

            pan, tilt, zoom = select_conf_by_id(user_id)

            isok, conf = controller.get_configuration()

            if isok:
                conf["pan"] = round(pan, 1)
                conf["tilt"] = round(tilt, 1)
                conf["zoom"] = round(zoom, 1)
                controller.configure(conf)
            else:
                raise ValueError(conf)

            frame = get_frame(ip2url(str(select_by_id(user_id, "camera_ip"))))
            bboxes = model.predict(frame)
            if len(bboxes) > 0:
                is_vehicle = False
                is_persen = False
                for i in np.unique(bboxes[:, 4]):
                    i = int(i)

                    if i in vehicles:
                        is_vehicle = True
                    elif i in people:
                        is_persen = True

                if is_vehicle and is_persen:
                    frame = draw_bboxes(frame, bboxes)
                    photo = Image.fromarray(frame)
                    text = "Vehicle and person are detected"
                    msg = bot.send_photo(user_id, photo, text)
                    if neet_email:
                        send_by_email(email, text)
                elif is_vehicle:
                    frame = draw_bboxes(frame, bboxes)
                    photo = Image.fromarray(frame)
                    text = "Vehicle is detected"
                    msg = bot.send_photo(user_id, photo, text)
                    if neet_email:
                        send_by_email(email, text)
                elif is_persen:
                    frame = draw_bboxes(frame, bboxes)
                    photo = Image.fromarray(frame)
                    text = "Person is detected"
                    msg = bot.send_photo(user_id, photo, text)
                    if neet_email:
                        send_by_email(email, text)

        except cv2.error as e:
            bot.send_message(user_id, "Failed to upload photo")

        except requests.exceptions.ConnectionError as e:
            bot.send_message(user_id, "Connection reset by peer")

        except Exception as e:
            bot.send_message(user_id, e)

        time.sleep(3)


def move_camera(message, controller):
    try:
        user_id = message.from_user.id
        user_name = message.from_user.username
        text = message.text.lower()
        if text == "stop":
            bot.send_message(user_id, "stopped", reply_markup=markup)
            update_by_id(user_id, "isRunning", 0)
            update_by_id(user_id, "msg_id", -1)
            return
        elif text == "show":
            pan, tilt, zoom = select_conf_by_id(user_id)

            isok, conf = controller.get_configuration()

            if isok:
                conf["pan"] = round(pan, 1)
                conf["tilt"] = round(tilt, 1)
                conf["zoom"] = round(zoom, 1)
                controller.configure(conf)
            else:
                raise ValueError(conf)

            photo = photo_by_url(ip2url(str(select_by_id(user_id, "camera_ip"))))
            bot.send_photo(user_id, photo, reply_markup=keyboard1)

            msg = delete_message(user_id, bot)
            bot.register_next_step_handler(
                msg, partial(move_camera, controller=controller)
            )
            return
        elif text == "track":

            print(text, user_id, user_name, select_by_id(user_id, "isTracking"))
            if not select_by_id(user_id, "isTracking"):

                msg = bot.send_message(
                    user_id, "started tracking", reply_markup=keyboard3
                )
                thread = Thread(target=track_loop, args=(user_id, controller))
                update_by_id(user_id, "isTracking", 1)
                bot.register_next_step_handler(
                    msg, partial(tracker_listener, controller=controller, thread=thread)
                )
                thread.start()
                return

        elif text == "zoom in":
            print(text, user_id, user_name)
            update_by_id(user_id, "zoom", float(select_by_id(user_id, "zoom")) + d_zoom)
        elif text == "zoom out":
            print(text, user_id, user_name)
            update_by_id(user_id, "zoom", float(select_by_id(user_id, "zoom")) - d_zoom)
        elif text == "right":
            print(text, user_id, user_name)
            update_by_id(user_id, "pan", float(select_by_id(user_id, "pan")) + d_pan)
        elif text == "left":
            print(text, user_id, user_name)
            update_by_id(user_id, "pan", float(select_by_id(user_id, "pan")) - d_pan)
        elif text == "up":
            print(text, user_id, user_name)
            update_by_id(user_id, "tilt", float(select_by_id(user_id, "tilt")) + d_tilt)
        elif text == "down":
            print(text, user_id, user_name)
            update_by_id(user_id, "tilt", float(select_by_id(user_id, "tilt")) - d_tilt)
        elif text.split()[0] == "preset":
            print(text, user_id, user_name)
            text_lst = text.split()
            if len(text_lst) > 1:
                isok, conf = controller.load_preset(text_lst[1])
            else:
                isok, conf = controller.load_preset("")

            if not isok:
                raise ValueError(conf)

            pan, tilt, zoom = conf["pan"], conf["tilt"], conf["zoom"]
            update_by_id(user_id, "pan", pan)
            update_by_id(user_id, "tilt", tilt)
            update_by_id(user_id, "zoom", zoom)

        else:
            bot.send_message(user_id, "Invalid operation.\nTry again or send stop")
            msg = delete_message(user_id, bot)
            bot.register_next_step_handler(
                msg, partial(move_camera, controller=controller)
            )
            return

        msg = delete_message(user_id, bot)
        bot.register_next_step_handler(msg, partial(move_camera, controller=controller))

    except cv2.error as e:
        msg = bot.reply_to(message, "Failed to upload photo\nTry again or send stop")
        bot.register_next_step_handler(msg, partial(move_camera, controller=controller))

    except requests.exceptions.ConnectionError as e:
        msg = bot.reply_to(message, "Connection reset by peer\nTry again or send stop")
        bot.register_next_step_handler(msg, partial(move_camera, controller=controller))

    except Exception as e:
        print(e)
        user_id = message.from_user.id
        bot.reply_to(message, f"{e}\nTry again or send stop")

        msg = delete_message(user_id, bot)
        bot.register_next_step_handler(msg, partial(move_camera, controller=controller))


def tracker_listener(message, controller, thread):
    print("tracker_listener")
    try:
        user_id = message.from_user.id
        user_name = message.from_user.username
        text = message.text.lower()
        msg = None
        if text == "stop":

            update_by_id(user_id, "isTracking", 0)
            thread.do_run = False
            thread.join()
            msg = bot.send_message(user_id, "Stopped tracking", reply_markup=keyboard1)
            bot.register_next_step_handler(
                msg, partial(move_camera, controller=controller)
            )
            return

        elif text == "show":
            pan, tilt, zoom = select_conf_by_id(user_id)

            isok, conf = controller.get_configuration()

            if isok:
                conf["pan"] = round(pan, 1)
                conf["tilt"] = round(tilt, 1)
                conf["zoom"] = round(zoom, 1)
                controller.configure(conf)
            else:
                raise ValueError(conf)

            global model
            frame = get_frame(ip2url(str(select_by_id(user_id, "camera_ip"))))
            bboxes = model.predict(frame)
            frame = draw_bboxes(frame, bboxes)
            photo = Image.fromarray(frame)
            msg = bot.send_photo(user_id, photo)
        else:
            msg = bot.send_message(
                user_id, "Tracking mode is enabled.\nPress stop to exit the mode"
            )
        bot.register_next_step_handler(
            msg, partial(tracker_listener, controller=controller, thread=thread)
        )

    except cv2.error as e:
        msg = bot.reply_to(message, "Failed to upload photo\nTry again or send stop")
        bot.register_next_step_handler(
            msg, partial(tracker_listener, controller=controller, thread=thread)
        )
        return

    except requests.exceptions.ConnectionError as e:
        msg = bot.reply_to(message, "Connection reset by peer\nTry again or send stop")
        bot.register_next_step_handler(
            msg, partial(tracker_listener, controller=controller, thread=thread)
        )

    except Exception as e:
        print(e)
        user_id = message.from_user.id
        msg = bot.reply_to(message, f"{e}\nTry again or send stop")
        bot.register_next_step_handler(
            msg, partial(tracker_listener, controller=controller, thread=thread)
        )
        return


# bot.polling(none_stop=True)
bot.polling(none_stop=False)


#################################
