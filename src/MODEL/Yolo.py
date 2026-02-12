import cv2
import torch
from ultralytics import YOLO
import numpy as np

class_names = ['line_mark', 'rust','defect']

def run_yolo_inference_single(model, image, conf_threshold: float = 0.4):

    if isinstance(image, str):
        img = cv2.imread(image)
    else:
        img = image

    if img is None:
        print("[⚠️] Couldn't load image.")
        return None, []

    results = model(img)
    predictions = results[0].boxes

    if predictions is None or len(predictions) == 0:
        print("[ℹ️] No detections in image.")
        return img, []

    bboxes = predictions.xyxy.cpu().numpy()
    scores = predictions.conf.cpu().numpy()
    labels = predictions.cls.cpu().numpy().astype(int)

    detected_labels = []
    for box, score, label in zip(bboxes, scores, labels):
        if score < conf_threshold:
            continue
        x1, y1, x2, y2 = map(int, box)
        class_name = class_names[label]
        detected_labels.append(class_name)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, f"{class_name} {score:.2f}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    return img, detected_labels
