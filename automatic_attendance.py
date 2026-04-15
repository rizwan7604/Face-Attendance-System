import os
import cv2
import csv
import pickle
from datetime import datetime, timedelta
import pandas as pd
from deepface import DeepFace
from config import *


# -------------------------
# GET STUDENT NAME
# -------------------------
def get_student_name(enrollment):
    try:
        df = pd.read_csv(STUDENT_DETAILS_PATH)
        df.columns = df.columns.str.strip()
        df["Enrollment"] = df["Enrollment"].astype(str).str.strip()

        row = df[df["Enrollment"] == str(enrollment).strip()]
        if not row.empty:
            return str(row.iloc[0]["Name"]).strip()
    except Exception as e:
        print("Name error:", e)

    return "Unknown"


# -------------------------
# EMOTION DETECTION
# -------------------------
def detect_emotion(face_img):
    try:
        result = DeepFace.analyze(
            face_img,
            actions=["emotion"],
            enforce_detection=False
        )

        if isinstance(result, list):
            result = result[0]

        return result.get("dominant_emotion", "unknown")

    except:
        return "unknown"


# -------------------------
# SAME SUBJECT SAME DAY CHECK
# -------------------------
def already_marked_same_subject_today(enrollment, subject, date_str):
    file_path = os.path.join(ATTENDANCE_PATH, f"{subject}_{date_str}.csv")

    if not os.path.exists(file_path):
        return False

    try:
        df = pd.read_csv(file_path)
        df["Enrollment"] = df["Enrollment"].astype(str).str.strip()

        if enrollment in df["Enrollment"].values:
            return True

    except:
        pass

    return False


# -------------------------
# OTHER SUBJECT COOLDOWN
# -------------------------
def cooldown_check(enrollment, current_subject, now):

    for file in os.listdir(ATTENDANCE_PATH):
        if not file.endswith(".csv"):
            continue

        try:
            df = pd.read_csv(os.path.join(ATTENDANCE_PATH, file))

            for _, row in df.iterrows():
                if str(row["Enrollment"]).strip() == enrollment:

                    old_subject = str(row["Subject"]).strip()

                    if old_subject == current_subject:
                        continue

                    record_time = datetime.strptime(
                        f"{row['Date']} {row['Time']}",
                        "%Y-%m-%d %H:%M:%S"
                    )

                    if (now - record_time).seconds < SUBJECT_COOLDOWN_SECONDS:
                        return True

        except:
            continue

    return False


# -------------------------
# SAVE ATTENDANCE
# -------------------------
def save_attendance(enrollment, name, subject, date, time, confidence, emotion):

    os.makedirs(ATTENDANCE_PATH, exist_ok=True)

    file_path = os.path.join(ATTENDANCE_PATH, f"{subject}_{date}.csv")

    file_exists = os.path.exists(file_path)

    with open(file_path, "a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "Enrollment", "Name", "Subject",
                "Date", "Time", "Confidence", "Emotion"
            ])

        writer.writerow([
            enrollment, name, subject,
            date, time, confidence, emotion
        ])


# -------------------------
# MAIN ATTENDANCE
# -------------------------
def start_attendance(subject):

    if not os.path.exists(MODEL_PATH):
        print("Model not found")
        return

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(MODEL_PATH)

    with open(LABELS_PATH, "rb") as f:
        label_map = pickle.load(f)

    cap = cv2.VideoCapture(CAMERA_INDEX)

    face_detector = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    marked_students = set()
    recent_display = {}

    print("Press ENTER to stop")

    while True:

        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_detector.detectMultiScale(gray, 1.3, 5)

        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M:%S")

        for (x, y, w, h) in faces:

            face = gray[y:y+h, x:x+w]
            face = cv2.resize(face, (200, 200))

            label, confidence = recognizer.predict(face)

            if confidence < FACE_CONFIDENCE_THRESHOLD:

                enrollment = str(label_map[label]).strip()
                name = get_student_name(enrollment)

                # display freeze (3 sec)
                if enrollment in recent_display:
                    status, color, expiry, emotion = recent_display[enrollment]

                    if now < expiry:
                        cv2.rectangle(frame, (x,y),(x+w,y+h), color,2)
                        cv2.putText(frame,f"{name} ({emotion})",(x,y-10),0,0.8,color,2)
                        cv2.putText(frame,status,(x,y+h+25),0,0.7,color,2)
                        continue
                    else:
                        del recent_display[enrollment]

                # SAME SESSION
                if enrollment in marked_students:
                    status = "Already Marked"
                    color = (0,255,255)
                    emotion = "-"

                # COOLDOWN
                elif cooldown_check(enrollment, subject, now):
                    status = "Wait"
                    color = (0,165,255)
                    emotion = "-"

                # SAME DAY SAME SUBJECT
                elif already_marked_same_subject_today(enrollment, subject, date):
                    marked_students.add(enrollment)
                    status = "Already Marked"
                    color = (0,255,255)
                    emotion = "-"

                else:
                    face_color = frame[y:y+h, x:x+w]
                    emotion = detect_emotion(face_color)

                    save_attendance(
                        enrollment,
                        name,
                        subject,
                        date,
                        time,
                        round(confidence,2),
                        emotion
                    )

                    marked_students.add(enrollment)

                    status = "Marked"
                    color = (0,255,0)

                    # freeze display
                    recent_display[enrollment] = (
                        status,
                        color,
                        now + timedelta(seconds=3),
                        emotion
                    )

                cv2.rectangle(frame, (x,y),(x+w,y+h), color,2)

                cv2.putText(frame,
                    f"{name} ({emotion})",
                    (x,y-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2
                )

                cv2.putText(frame,
                    status,
                    (x,y+h+25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    color,
                    2
                )

            else:
                cv2.putText(frame,"Unknown",(x,y-10),0,0.8,(0,0,255),2)

        cv2.putText(frame,f"Subject: {subject}",(20,30),0,0.8,(255,255,255),2)
        cv2.putText(frame,"Press ENTER to stop",(20,60),0,0.7,(255,255,255),2)

        cv2.imshow("Attendance", frame)

        if cv2.waitKey(1) & 0xFF == 13:
            break

    cap.release()
    cv2.destroyAllWindows()