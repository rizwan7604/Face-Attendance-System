import os
import csv
import cv2
import pickle
import pandas as pd
from tkinter import messagebox
from config import *

def is_duplicate_face_from_model(face_detector, cap, new_enrollment):

    if not os.path.exists(MODEL_PATH) or not os.path.exists(LABELS_PATH):
        return False

    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read(MODEL_PATH)

        with open(LABELS_PATH, "rb") as file:
            label_map = pickle.load(file)

    except Exception as e:
        print("Duplicate model load error:", e)
        return False

    prediction_counts = {}
    checked_frames = 0
    max_checks = 15   # more frames = better accuracy

    while checked_frames < max_checks:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_detector.detectMultiScale(
            gray,
            scaleFactor=1.3,
            minNeighbors=5,
            minSize=(100, 100)
        )

        display_frame = frame.copy()

        if len(faces) == 1:
            x, y, w, h = faces[0]
            face = gray[y:y + h, x:x + w]

            try:
                face = cv2.resize(face, (200, 200))
                label, confidence = recognizer.predict(face)

                # 🔥 VERY IMPORTANT CHANGE
                # Strict condition (avoid false detection)
                if confidence < 45 and label in label_map:

                    predicted_enrollment = str(label_map[label]).strip()

                    if predicted_enrollment != new_enrollment:
                        prediction_counts[predicted_enrollment] = (
                            prediction_counts.get(predicted_enrollment, 0) + 1
                        )

                checked_frames += 1

                cv2.putText(display_frame, f"Confidence: {int(confidence)}",
                            (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

            except Exception as e:
                print("Duplicate prediction error:", e)

        else:
            cv2.putText(display_frame, "Show only one face",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

        cv2.imshow("Duplicate Check", display_frame)

        if cv2.waitKey(1) & 0xFF == 13:
            return False

    if not prediction_counts:
        return False

    most_likely = max(prediction_counts, key=prediction_counts.get)
    count = prediction_counts[most_likely]

    # 🔥 FINAL DECISION (more strict)
    return count >= 6


def capture_student_face(enrollment, name):
    enrollment = enrollment.strip()
    name = name.strip()

    if not enrollment.isdigit() or len(enrollment) != 6:
        messagebox.showerror("Error", "Enrollment must be exactly 6 digits")
        return False

    if name == "":
        messagebox.showerror("Error", "Student name required")
        return False

    if not os.path.exists(MASTER_DATA_PATH):
        messagebox.showerror("Error", "Master data file not found")
        return False

    # Master data validation
    try:
        master_df = pd.read_csv(MASTER_DATA_PATH)
        master_df.columns = master_df.columns.str.strip()

        required_columns = ["Enrollment", "Name"]
        for col in required_columns:
            if col not in master_df.columns:
                messagebox.showerror(
                    "Master Data Error",
                    f"Missing column: {col} in student_list.csv"
                )
                return False

        master_df["Enrollment"] = master_df["Enrollment"].astype(str).str.strip()
        master_df["Name"] = master_df["Name"].astype(str).str.strip()

        matched_student = master_df[
            (master_df["Enrollment"] == enrollment) &
            (master_df["Name"].str.lower() == name.lower())
        ]

        if matched_student.empty:
            messagebox.showerror(
                "Validation Error",
                "Student not found in Master Data.\nPlease check Enrollment Number and Name."
            )
            return False

    except Exception as e:
        messagebox.showerror("Master Data Error", str(e))
        return False

    # Create required folders
    student_details_folder = os.path.dirname(STUDENT_DETAILS_PATH)
    if student_details_folder:
        os.makedirs(student_details_folder, exist_ok=True)

    os.makedirs(TRAINING_IMAGE_PATH, exist_ok=True)

    # Create or repair student details CSV
    if not os.path.exists(STUDENT_DETAILS_PATH) or os.path.getsize(STUDENT_DETAILS_PATH) == 0:
        with open(STUDENT_DETAILS_PATH, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Enrollment", "Name"])

    try:
        df = pd.read_csv(STUDENT_DETAILS_PATH)
        df.columns = [col.strip() for col in df.columns]

        if len(df.columns) < 2:
            with open(STUDENT_DETAILS_PATH, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Enrollment", "Name"])
        else:
            df.columns = ["Enrollment", "Name"]
            df.to_csv(STUDENT_DETAILS_PATH, index=False)

    except Exception as e:
        print("CSV repair error:", e)
        with open(STUDENT_DETAILS_PATH, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Enrollment", "Name"])

    # Duplicate enrollment check
    try:
        df = pd.read_csv(STUDENT_DETAILS_PATH)

        if "Enrollment" not in df.columns:
            df.columns = ["Enrollment", "Name"]

        df["Enrollment"] = df["Enrollment"].astype(str).str.strip()

        if enrollment in df["Enrollment"].values:
            messagebox.showwarning("Duplicate", "Student already registered")
            return False

    except Exception as e:
        messagebox.showerror("CSV Error", str(e))
        return False

    # Student image folder
    student_folder = os.path.join(TRAINING_IMAGE_PATH, enrollment)
    os.makedirs(student_folder, exist_ok=True)

    # Clear old images if any
    try:
        for file_name in os.listdir(student_folder):
            file_path = os.path.join(student_folder, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)
    except Exception as e:
        messagebox.showerror("Folder Error", f"Unable to prepare student folder\n{str(e)}")
        return False

    # Camera start
    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        messagebox.showerror("Camera Error", "Unable to access camera")
        return False

    face_detector = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    # Better duplicate check
    try:
        duplicate_found = is_duplicate_face_from_model(face_detector, cap, enrollment)
        if duplicate_found:
            cap.release()
            cv2.destroyAllWindows()
            messagebox.showerror(
                "Duplicate Face",
                "This face already looks registered in the system."
            )
            return False
    except Exception as e:
        print("Duplicate check skipped:", e)

    count = 0
    frame_counter = 0

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            faces = face_detector.detectMultiScale(
                gray,
                scaleFactor=1.3,
                minNeighbors=5,
                minSize=(100, 100)
            )

            if len(faces) > 1:
                cv2.putText(
                    frame,
                    "Only One Face Allowed",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2
                )

            elif len(faces) == 1:
                for (x, y, w, h) in faces:
                    face = gray[y:y + h, x:x + w]

                    try:
                        face = cv2.resize(face, (200, 200))
                    except Exception as e:
                        print("Resize error:", e)
                        continue

                    frame_counter += 1

                    if frame_counter % 3 == 0 and count < MAX_FACE_SAMPLES:
                        count += 1
                        image_path = os.path.join(student_folder, f"{count}.jpg")
                        cv2.imwrite(image_path, face)

                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    cv2.putText(
                        frame,
                        f"Captured: {count}/{MAX_FACE_SAMPLES}",
                        (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 255, 0),
                        2
                    )

                    cv2.putText(
                        frame,
                        "Press ENTER to stop",
                        (20, 75),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.65,
                        (255, 255, 255),
                        2
                    )

                    cv2.putText(
                        frame,
                        "Keep face centered and look around slightly",
                        (20, 105),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.60,
                        (255, 255, 255),
                        2
                    )

            else:
                cv2.putText(
                    frame,
                    "Show only one face to camera",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2
                )

                cv2.putText(
                    frame,
                    "Press ENTER to stop",
                    (20, 75),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (255, 255, 255),
                    2
                )

            cv2.imshow("Face Registration", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == 13:
                break

            if count >= MAX_FACE_SAMPLES:
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()

    if count < MIN_FACE_SAMPLES:
        messagebox.showwarning(
            "Incomplete",
            f"Only {count} images captured. Minimum {MIN_FACE_SAMPLES} required."
        )
        return False

    # Save student data
    try:
        with open(STUDENT_DETAILS_PATH, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([enrollment, name])
    except Exception as e:
        messagebox.showerror("Save Error", f"Unable to save student data\n{str(e)}")
        return False

    messagebox.showinfo(
        "Success",
        f"{name} registered successfully with {count} face samples"
    )

    return True