import os
import cv2
import pickle
import numpy as np
from tkinter import messagebox
from config import *


def train_face_model():

    image_data = []
    labels = []
    label_map = {}

    if not os.path.exists(TRAINING_IMAGE_PATH):
        messagebox.showerror("Error", "TrainingImage folder not found")
        return False

    student_folders = os.listdir(TRAINING_IMAGE_PATH)

    if len(student_folders) == 0:
        messagebox.showerror("Error", "No student images found")
        return False

    recognizer = cv2.face.LBPHFaceRecognizer_create()

    current_label = 0

    for folder in student_folders:

        folder_path = os.path.join(TRAINING_IMAGE_PATH, folder)

        if not os.path.isdir(folder_path):
            continue

        label_map[current_label] = folder

        for image_name in os.listdir(folder_path):

            image_path = os.path.join(folder_path, image_name)

            try:
                img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

                if img is None:
                    continue

                img = cv2.resize(img, (200, 200))

                image_data.append(img)
                labels.append(current_label)

            except:
                continue

        current_label += 1

    if len(image_data) == 0:
        messagebox.showerror("Error", "No valid training images found")
        return False

    try:
        recognizer.train(image_data, np.array(labels))
    except Exception as e:
        messagebox.showerror("Training Error", str(e))
        return False

    # -------------------------
    # MODEL FOLDER CREATE
    # -------------------------
    os.makedirs("model", exist_ok=True)

    try:
        # SAVE MODEL (.yml)
        recognizer.save(MODEL_PATH)

        # SAVE LABEL MAP
        with open(LABELS_PATH, "wb") as file:
            pickle.dump(label_map, file)

    except Exception as e:
        messagebox.showerror("Save Error", str(e))
        return False

    messagebox.showinfo(
        "Success",
        f"Model trained successfully\n\nStudents: {len(student_folders)}\nImages Used: {len(image_data)}"
    )

    return True