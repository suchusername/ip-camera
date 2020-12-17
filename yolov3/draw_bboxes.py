import numpy as np
import cv2
import warnings
import os.path as osp
import pandas as pd
from matplotlib import colors as mp_colors
from matplotlib import cm as mp_cm
from matplotlib import pyplot as plt

DEFAULT_NAMING_PATH = "/ip-camera/yolov3/config/coco_naming.csv"


def getClasses(path):
    df = pd.read_csv(path)
    return df["visualization_name"].to_dict()


def dashed_line(img, pt1, pt2, color, dash_length=15, dash_interval=15, **kwargs):
    """
    Wrapper for cv2.line() for drawing dashed lines.
    
    Args:
    img          : np.array of shape (?,?,3) with image values
    pt1          : tuple (x,y), coordinates of first endpoint
    pt2          : tuple (x,y), coordinates of second endpoint
    color        : [R, G, B]
    dash_length  : int, length of a dash
    dash_interval: int, length of an interval between dashes
    kwargs       : dict, any extra keyword arguments that can be passed in cv2.line()
    """

    np_pt1 = np.array(pt1)
    np_pt2 = np.array(pt2)
    line_length = np.sqrt(((np_pt1 - np_pt2) ** 2).sum())
    get_point = lambda s: np_pt1 + s / line_length * (np_pt2 - np_pt1)
    # returns a point which is s units away from pt1

    covered = 0
    segments = []
    while covered < line_length:
        p1 = get_point(covered)
        covered = min(line_length, covered + dash_length)
        p2 = get_point(covered)
        covered += dash_interval
        segments.append((tuple(p1.astype(int)), tuple(p2.astype(int))))

    # making last dash go until the end

    segments[-1] = (segments[-1][0], tuple(get_point(line_length).astype(int)))

    for p1, p2 in segments:
        cv2.line(img, p1, p2, color, **kwargs)


def dashed_rectangle(img, pt1, pt2, color, dash_length=15, dash_interval=15, **kwargs):
    """
    Wrapper for cv2.line() for drawing dashed rectangles.
    
    Args:
    img          : np.array of shape (?,?,3) with image values
    pt1          : tuple (x,y), coordinates of one corner
    pt2          : tuple (x,y), coordinates of another corner
    color        : [R, G, B]
    dash_length  : int, length of a dash
    dash_interval: int, length of an interval between dashes
    kwargs       : dict, any extra keyword arguments that can be passed in cv2.line()
    """
    x_min = min(pt1[0], pt2[0])
    x_max = max(pt1[0], pt2[0])
    y_min = min(pt1[1], pt2[1])
    y_max = max(pt1[1], pt2[1])

    segments = [
        ((x_min, y_min), (x_max, y_min)),
        ((x_max, y_min), (x_max, y_max)),
        ((x_max, y_max), (x_min, y_max)),
        ((x_min, y_max), (x_min, y_min)),
    ]

    for p1, p2 in segments:
        dashed_line(img, p1, p2, color, dash_length, dash_interval, **kwargs)


def draw_bboxes(
    image,
    bboxes,
    colors=None,
    color_by="class",
    show_desc=True,
    show_label=True,
    show_conf=True,
    show_trackid=True,
    naming_path=DEFAULT_NAMING_PATH,
    colormap="gist_ncar",
    line_thickness=None,
    style=None,
    desc_scale=1,
    desc_style=0,
):
    """
    Draws bounding boxes, confidence and labels on an image. Label names are taken from the file `naming_csv`
    
    Arguments:
    image         : np.array of shape (?,?,3) with np.uint8 data type in RGB format, 
        otherwise it is assumed that normalized image is given.
    bboxes        : list or numpy array with columns [x_min, y_min, width, height, label, score, track_id],
        where (x_min, y_min) are coordinates of top left corner,
              label - an integer encoding a class, if missing, it is 0 by default ('person'),
              score - confidence of a prediction, a float in [0,1]
              track_id - an integer encoding a track that this bbox belongs to
        Last 3 columns are optional.
    colors        : a list of color names for different classes of bboxes (Ex: ['red', 'blue']),
        for color names refer to https://matplotlib.org/3.1.0/gallery/color/named_colors.html
    color_by      : "class" or "track", which category is supposed to have different colors (default: "class")
    show_desc     : whether to draw description (class label, confidence and track id) or not
    show_label    : whether to draw labels with classes or not
    show_conf    : whether to show confidence score or not
    show_trackid  : whether to show track id or not
    naming_path   : path to file with labels
    colormap      : str, name of matplotlib colormap to use (default: "gist_ncar")
    line_thickness: int, thickness of a bounding box in pixels (default is determined by image size)
    style         : str, None or "dashed" (default: None)
    desc_scale    : float, size of description relative to automatic size (default: 1),
    desc_style    : 0 or 1, two different styles of description (default: 0)
                                        
    Returns:
    transformed numpy array of shape (?,?,3) with image data of type np.uint8
    """
    # # 1. Input preparation

    # Converting to np.uint8
    if image.dtype != np.uint8:
        warnings.warn(
            "Converting image to np.uint8 myself assuming [0,1] range, can break something, consider converting yourself"
        )
        image = np.clip((image * 255).astype(np.uint8), 0, 255)
    else:
        image = image.copy()

    # checking arguments
    if style not in [None, "dashed"]:
        raise ValueError(
            f"Unknown style `{style}`. It must be either None or `dashed`."
        )
    if color_by not in ["class", "track"]:
        raise ValueError(
            f"Unknown color target `{color_by}`. It must be either `class` or `track`."
        )
    if color_by == "track" and bboxes.shape[1] < 7:
        raise ValueError(
            f"Cannot set color target to `track`, because bboxes do not have track ids."
        )
    if bboxes.shape[1] < 7:
        show_trackid = False
        if bboxes.shape[1] < 6:
            show_conf = False
    if desc_style not in [0, 1]:
        raise ValueError(
            f"Unknown description style `{desc_style}`. It must be either 0 or 1."
        )

    bboxes = bboxes[bboxes.sum(axis=1) > 0]

    # clipping bboxes
    image_h, image_w, _ = image.shape
    bboxes[:, 2:4] += bboxes[:, 0:2]
    bboxes[:, [0, 2]] = np.clip(bboxes[:, [0, 2]], 1, image_w - 1)
    bboxes[:, [1, 3]] = np.clip(bboxes[:, [1, 3]], 1, image_h - 1)
    bboxes[:, 2:4] -= bboxes[:, 0:2]

    if bboxes.shape[1] >= 6:
        asrt = np.argsort(bboxes[:, 5])
        bboxes = bboxes[asrt]

    # add class label (adding 0s), if it is missing
    if bboxes.shape[1] == 4:
        bboxes = np.concatenate(
            [bboxes, np.zeros((bboxes.shape[0], 1), dtype=bboxes.dtype),], axis=-1,
        )

    # getting classes dict {label: name}, if naming.csv is not passed then it is {label: label}
    if naming_path is not None:
        classes = getClasses(naming_path)
        # checking if bboxes have classes that are not in naming.csv. If there are, they are added as {label:label}
        present_classes = np.unique(bboxes[:, 4]).astype(int)
        warned = False
        for c in present_classes:
            if c not in classes.keys():
                if not warned:
                    warnings.warn(
                        "Bboxes have class labels which are not described in naming.csv."
                    )
                    warned = True
                classes[c] = str(c)
    else:
        classes = {0: "h"}
        # if len(bboxes) > 0:
        #    classes = {int(c): str(int(c)) for c in np.unique(bboxes[:, 4])}

    # setting colors, it is dict {label: color},
    # where color is np.array of shape (3,) with R, G, B values in [0, 255] range
    if color_by == "class":
        color_by_col = 4
    elif color_by == "track":
        color_by_col = 6
    present_categories = np.unique(bboxes[:, color_by_col]).astype(int)

    if colors is None:
        # automatically loading colors from colormap
        colormap = mp_cm.get_cmap(colormap)

        def label_to_color(c):
            idx = 0.8 * int(format(c, "016b")[::-1], 2) / (2 ** 16) + 0.2
            return np.array(colormap(idx)[:3]) * 255

        colors_dict = {int(c): label_to_color(c) for c in present_categories}

    else:
        # colors are specified by user
        if len(colors) < len(present_categories):
            raise ValueError(
                f"Not enough colors are specified. Bboxes have {len(present_categories)} different categories."
            )
        colors = colors[: len(present_categories)]
        colors_dict = {
            int(c): (np.array(mp_colors.to_rgb(col)) * 255)
            for c, col in zip(present_categories, colors)
        }

    # setting writing and drawing arguments
    fontscale = (image_h / 1200.0) * desc_scale

    if line_thickness is None:
        line_thickness = max(1, round(0.8 * (image_h + image_w) / 600))
    font = cv2.FONT_HERSHEY_SIMPLEX

    # # 2. Drawing bboxes

    for bbox in bboxes:

        # drawing a bounding box
        c0 = (int(bbox[0]), int(bbox[1]))  # top left
        c1 = (int(bbox[0]) + int(bbox[2]), int(bbox[1]) + int(bbox[3]))  # bottom right
        bbox_color = colors_dict[int(bbox[color_by_col])]

        if style == "dashed":
            dashed_rectangle(image, c0, c1, bbox_color, thickness=line_thickness)
        else:
            cv2.rectangle(image, c0, c1, bbox_color, line_thickness)

    # # 3. Drawing descriptions

    if show_desc:

        for bbox in bboxes:

            c0 = (int(bbox[0]), int(bbox[1]))  # top left
            c1 = (
                int(bbox[0]) + int(bbox[2]),
                int(bbox[1]) + int(bbox[3]),
            )  # bottom right
            bbox_label = int(bbox[4])
            bbox_color = colors_dict[int(bbox[color_by_col])]

            messages = []
            messages_fontscale = []
            if show_label:
                messages.append(classes[bbox_label])
                messages_fontscale.append(fontscale)
            if show_conf:
                bbox_conf = bbox[5]
                messages.append(str(int(round(bbox_conf, 2) * 100)) + "%")
                messages_fontscale.append(fontscale * 0.6)
            if show_trackid:
                bbox_trackid = bbox[6]
                messages.append("#" + str(int(bbox_trackid)))
                messages_fontscale.append(fontscale * 0.6)

            if len(messages) > 0:

                messages_size = [
                    cv2.getTextSize(msg, font, messages_fontscale[i], thickness=1)[0]
                    for i, msg in enumerate(messages)
                ]
                max_message_length = max([w for w, h in messages_size])

                # calculating positions for text
                messages_coords = []
                y_pos = c0[1]  # y-coord of top corner of bbox

                if (c1[0] + max_message_length + 3 <= image_w) and (
                    (bbox_label == 0) or (c0[0] - max_message_length - 5 < 0)
                ):
                    right_pos = True
                else:
                    right_pos = False

                for size in messages_size:
                    y_pos += size[1]
                    if right_pos:
                        # description is to the right of bbox
                        text_c = (
                            c1[0] + 5,  # x-coord of bottom left corner of text
                            y_pos,  # y-coord
                        )
                    else:
                        # description is to the left of bbox
                        text_c = (
                            c0[0]
                            - 5
                            - size[0],  # x-coord of bottom left corner of text
                            y_pos,  # y-coord
                        )
                    y_pos += 5 * desc_scale
                    messages_coords.append(text_c)

                # adding some background
                if desc_style == 0:

                    bg_top = c0[1]
                    bg_bottom = y_pos
                    bg_left = c1[0] if right_pos else (c0[0] - max_message_length - 5)
                    bg_right = bg_left + max_message_length + 6
                    sub_image = np.array(
                        image[bg_top:bg_bottom, bg_left:bg_right], dtype=np.uint8
                    )
                    bg_rect = np.concatenate(
                        [
                            np.ones(shape=(sub_image.shape[0], sub_image.shape[1], 1))
                            * bbox_color[0],
                            np.ones(shape=(sub_image.shape[0], sub_image.shape[1], 1))
                            * bbox_color[1],
                            np.ones(shape=(sub_image.shape[0], sub_image.shape[1], 1))
                            * bbox_color[2],
                        ],
                        axis=-1,
                    ).astype(np.uint8)
                    bg_res = cv2.addWeighted(sub_image, 0.4, bg_rect, 0.6, 1.0)
                    image[bg_top:bg_bottom, bg_left:bg_right] = bg_res

                # putting text
                if desc_style == 0:

                    for i in range(len(messages)):
                        cv2.putText(
                            image,
                            messages[i],
                            messages_coords[i],
                            font,
                            messages_fontscale[i],
                            (0, 0, 0),
                            thickness=1,
                            lineType=cv2.LINE_AA,
                        )

                elif desc_style == 1:

                    for i in range(len(messages)):
                        cv2.putText(
                            image,
                            messages[i],
                            messages_coords[i],
                            font,
                            messages_fontscale[i],
                            (0, 0, 0),
                            thickness=3,
                            lineType=cv2.LINE_AA,
                        )
                    for i in range(len(messages)):
                        cv2.putText(
                            image,
                            messages[i],
                            messages_coords[i],
                            font,
                            messages_fontscale[i],
                            bbox_color,
                            thickness=2,
                            lineType=cv2.LINE_AA,
                        )

    return image
