import cv2
import numpy as np
from PIL import Image
import sqlite3 as lite


def photo_by_url(stream_url):
    print("Starting the download")
    cap = cv2.VideoCapture(stream_url)
    while True:

        ret, frame = cap.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        break
    print("Download completed")
    return Image.fromarray(frame)


def new_users(user_id, username, stream_url, isRunning, data_users = 'data_users.db'):  
    con = lite.connect(data_users)
    cur = con.cursor()
    cur.execute("select user_id from users WHERE user_id = ?", (user_id,))

    if not (user_id,) in cur.fetchall():
        con = lite.connect(data_users)
        cur = con.cursor()
        cur.execute("INSERT INTO users VALUES(?, ?, ?, ?)",
            (user_id, username, stream_url, isRunning))
        con.commit()

        
def update_by_id(user_id, column_name, value, table='users', data_users='data_users.db'):
    con = lite.connect(data_users)
    cur = con.cursor()
    cur.execute(f'UPDATE {table} SET {column_name}=? WHERE user_id=?', (value, user_id,))
    con.commit()

    
def select_by_id(user_id, column_name, table='users', data_users='data_users.db'):
    
    con = lite.connect(data_users)
    cur = con.cursor()
    recs = cur.execute(f'SELECT {column_name} FROM {table} WHERE user_id={user_id}').fetchall()
    
    return recs[0][0]


