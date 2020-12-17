import cv2
import numpy as np
from PIL import Image
from db_tools import select_by_id, select_conf_by_id, update_by_id

def photo_by_url(stream_url):
    print("Starting the download")
    cap = cv2.VideoCapture(stream_url)
    ret, frame = cap.read()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    print("Download completed")
   
    return Image.fromarray(frame)


def delete_message(user_id, bot):
    bot.delete_message(user_id,  str(select_by_id(user_id, 'msg_id')))
    pan, tilt, zoom = select_conf_by_id(user_id)
    msg = bot.send_message(user_id, f'pan={pan},\ntilt={tilt},\nzoom={zoom}')
    update_by_id(user_id, 'msg_id', msg.id)
    return msg
