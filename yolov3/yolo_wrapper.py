import os
import numpy as np
import tensorflow as tf
import json
import wget

import yolov3.core.utils as utils
from yolov3.core.yolov3 import YOLOv3, decode

YOLO_CONFIG = "/ip-camera/config/yolov3_config.json"


class YOLOv3Wrapper:
    """
    A TensorFlow wrapper for YOLOv3 model.
    
    Args: None
    
    Attributes:
    config: dict, model configuration
    model : instance of tensorflow.keras.Model
    """

    def __init__(self):

        with open(YOLO_CONFIG, "r") as fd:
            config = json.load(fd)
        self.config = config

        input_size = config["input_size"]
        if input_size not in [320, 416, 608]:
            raise ValueError("input_size must be one of 320, 416, 608.")

        tf.keras.backend.clear_session()

        self.input_size = input_size
        input_layer = tf.keras.layers.Input([self.input_size, self.input_size, 3])
        feature_maps = YOLOv3(input_layer)

        bbox_tensors = []
        for i, fm in enumerate(feature_maps):
            bbox_tensor = decode(fm, i)
            bbox_tensors.append(bbox_tensor)

        self.model = tf.keras.Model(input_layer, bbox_tensors)

        if not os.path.exists(config["weights_path"]):
            print("Downloading YOLOv3 weights...")
            wget.download(config["weights_url"], out=config["weights_path"])

        utils.load_weights(self.model, config["weights_path"])

    def predict(self, image):
        """
        Run a detector on a raw image with all pre- and postprocessing.
        
        Args:
        image            : np.array with an RGB image,
        
        Returns:
        (bboxes, image), where
            bboxes: numpy array of shape (?,6) with columns [x_min, y_min, width, height, score, label],
                where (x_min, y_min) is a top left corner of a bounding box,
            image: a PIL image object with drawn bounding boxes
        """

        original_image_size = image.shape[:2]
        image = utils.image_preprocess(
            np.copy(image), [self.input_size, self.input_size]
        )
        image = image[np.newaxis, ...].astype(np.float32)

        pred_bbox = self.model.predict(image)
        pred_bbox = [tf.reshape(x, (-1, tf.shape(x)[-1])) for x in pred_bbox]
        pred_bbox = tf.concat(pred_bbox, axis=0)

        bboxes = utils.postprocess_boxes(
            pred_bbox,
            original_image_size,
            self.config["input_size"],
            self.config["score_threshold"],
        )

        bboxes[:, [4, 5]] = bboxes[:, [5, 4]]

        bboxes = utils.nms(np.copy(bboxes), self.config["nms_iou_threshold"])

        bboxes[:, [2, 3]] = bboxes[:, [2, 3]] - bboxes[:, [0, 1]]

        return bboxes
