import cv2
import numpy as np
from PIL import Image


def photo_by_url(stream_url):
    cap = cv2.VideoCapture(stream_url)
    while True:

        ret, frame = cap.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        break
    return Image.fromarray(frame)