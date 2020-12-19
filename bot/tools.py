import cv2
import numpy as np
import smtplib
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
    bot.delete_message(user_id, str(select_by_id(user_id, "msg_id")))
    pan, tilt, zoom = select_conf_by_id(user_id)
    pan = round(pan, 1)
    tilt = round(tilt, 1)
    zoom = round(zoom, 1)

    msg = bot.send_message(user_id, f"pan={pan},\ntilt={tilt},\nzoom={zoom}")
    update_by_id(user_id, "msg_id", msg.id)
    return msg


email = 'incredible.ip.camera.bot@gmail.com'
password = 'incredible_ip_camera_bot0'

def send_by_email(to_email, text):
    try:
        print(to_email, text)
        smtpserver = smtplib.SMTP("smtp.gmail.com", 587)
        smtpserver.ehlo()
        smtpserver.starttls()
        smtpserver.ehlo()
        smtpserver.login(email, password)
        smtpserver.sendmail(email, to_email, text)  
        smtpserver.quit()
    except Exception as e:
        print(e)
#         raise ValueError("Invalid email")