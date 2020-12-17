import cv2
import time
import json
import PIL
import multiprocessing
import numpy as np

from yolov3.draw_bboxes import draw_bboxes


IO_CONFIG_PATH = "/ip-camera/config/io_config.json"
with open(IO_CONFIG_PATH, "r") as fd:
    TRACKING_CONFIG = json.load(fd)["tracking"]


def get_frame(stream_url, verbose=False):
    """
    Get a frame from a video stream.
    
    Args:
    stream_url: str
    verbose   : bool
    
    Returns:
    np.array of shape (h, w, 3) with RGB image
        or None, if failed to load frame
    """
    if verbose:
        print("Downloading frame...", end=" ")

    cap = cv2.VideoCapture(stream_url)
    ret, frame = cap.read()
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    else:
        if verbose:
            print("failed.")
        return None

    if verbose:
        print("done.")
    return frame


def detect(model, bot, frame, with_photos):
    """
    Run detection on an image and log results.
    """
    bboxes = model.predict(frame)
    img = draw_bboxes(frame, bboxes)

    if with_photos:
        # bot sends `img`
        print("photo")
        pass
    else:
        # bot sends some text...
        print(bboxes.shape)
        pass


def tracking(model, bot, url, t=None, with_photos=None):
    """
    Start tracking on the video.
    
    Args:
    model      : YOLOv3Wrapper instance
    bot        : Telegram bot instance that will output the results
    url        : str, stream URL
    t          : duration of tracking
    with_photos: bool, whether to send an image or text
    """

    t_start = time.time()
    t_now = t_start

    # default arguments
    if t is None:
        t = TRACKING_CONFIG["default_time"]
    if with_photos is None:
        with_photos = TRACKING_CONFIG["with_photos"]

    cap = cv2.VideoCapture(url)

    interval = TRACKING_CONFIG["interval"]
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_n = 0
    freq = int(interval * fps)

    process_detect = None

    while t_now < t_start + t:

        ok, frame = cap.read()
        print(frame_n)

        frame_n += 1
        if (frame_n - 1) % freq != 0:
            continue

        if not ok:
            # log that frame was not parsed, also log `t_now` variable
            continue

        try:
            process_detect.join()
        except:
            pass

        print("detecting...")

        process_detect = multiprocessing.Process(
            target=detect, args=(model, bot, frame, with_photos)
        )
        process_detect.start()

        t_now = time.time()

    try:
        process_detect.join()
    except:
        pass
