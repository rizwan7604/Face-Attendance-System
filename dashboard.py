from register_student import capture_student_face
from train_image import train_face_model
from automatic_attendance import start_attendance
from reports import load_reports_ui
import customtkinter as ctk
import pandas as pd
import os
from datetime import datetime
from tkinter import messagebox
from config import *
from reports import calculate_attendance_stats


class Dashboard:
    def __init__(self, root):
        self.root = root

        self.frame = ctk.CTkFrame(root, fg_color=BG_COLOR)
        self.frame.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = ctk.CTkFrame(
            self.frame,
            width=220,
            fg_color=CARD_COLOR,
            corner_radius=0
        )
        self.sidebar.pack(side="left", fill="y")

        ctk.CTkLabel(
            self.sidebar,
            text="Dashboard",
            font=("Arial", 24, "bold"),
            text_color=TEXT_COLOR
        ).pack(pady=(30, 30))

        menu_items = [
            ("Register Student", self.show_register_screen),
            ("Train Model", self.train_model),
            ("Take Attendance", self.take_attendance),
            ("Reports", self.show_reports),
            ("Logout", self.logout)
        ]

        for text, command in menu_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                width=180,
                height=45,
                fg_color=ACCENT_COLOR,
                hover_color="#3730A3",
                command=command
            )
            btn.pack(pady=10)

        self.content = ctk.CTkFrame(
            self.frame,
            fg_color=BG_COLOR
        )
        self.content.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        self.load_home()

    # ------------------------
    # COMMON
    # ------------------------
    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def create_back_button(self, parent):
        ctk.CTkButton(
            parent,
            text="Back",
            width=100,
            height=38,
            fg_color=ACCENT_COLOR,
            hover_color="#3730A3",
            command=self.load_home
        ).pack(side="right", padx=10)

    # ------------------------
    # HOME
    # ------------------------
    def load_home(self):
        self.clear_content()

        total_students = 0
        total_reports = 0
        today_attendance = 0
        today = datetime.now().strftime("%Y-%m-%d")

        if os.path.exists(STUDENT_DETAILS_PATH):
            try:
                df = pd.read_csv(STUDENT_DETAILS_PATH)
                total_students = len(df)
            except Exception as e:
                print("Student count error:", e)

        if os.path.exists(ATTENDANCE_PATH):
            try:
                for root, dirs, files in os.walk(ATTENDANCE_PATH):
                    for file in files:
                        if file.endswith(".csv"):
                            total_reports += 1
                            try:
                                df = pd.read_csv(os.path.join(root, file))
                                if "Date" in df.columns:
                                    today_attendance += (
                                        df["Date"].astype(str).str.strip() == today
                                    ).sum()
                            except Exception as e:
                                print("Attendance file error:", e)
            except Exception as e:
                print("Attendance folder error:", e)

        top_bar = ctk.CTkFrame(self.content, fg_color=BG_COLOR)
        top_bar.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            top_bar,
            text="Welcome to Smart Attendance System",
            font=("Arial", 28, "bold"),
            text_color=TEXT_COLOR
        ).pack(side="left", padx=10)

        # CENTER TITLE
        ctk.CTkLabel(
            self.content,
            text="Facial Attendance and Sentiment Tracking via expression recognition",
            font=("Arial", 20, "bold"),
            text_color=TEXT_COLOR,
            wraplength=700,
            justify="center"
        ).pack(pady=20)

        card_frame = ctk.CTkFrame(self.content, fg_color=BG_COLOR)
        card_frame.pack(pady=20)

        cards = [
            ("Registered Students", str(total_students)),
            ("Today's Attendance", str(today_attendance)),
            ("Reports", str(total_reports)),
            ("Subjects", str(len(SUBJECTS)))
        ]

        for i, (title, value) in enumerate(cards):
            card = ctk.CTkFrame(
                card_frame,
                width=190,
                height=120,
                fg_color=CARD_COLOR,
                corner_radius=15
            )
            card.grid(row=0, column=i, padx=15, pady=10)
            card.grid_propagate(False)

            ctk.CTkLabel(
                card,
                text=title,
                font=("Arial", 16),
                text_color=SECONDARY_TEXT
            ).pack(pady=(25, 10))

            ctk.CTkLabel(
                card,
                text=value,
                font=("Arial", 28, "bold"),
                text_color=TEXT_COLOR
            ).pack()

    # ------------------------
    # REGISTER
    # ------------------------
    def show_register_screen(self):
        self.clear_content()

        top_bar = ctk.CTkFrame(self.content, fg_color=BG_COLOR)
        top_bar.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            top_bar,
            text="Register Student",
            font=("Arial", 28, "bold"),
            text_color=TEXT_COLOR
        ).pack(side="left", padx=10)

        self.create_back_button(top_bar)

        form = ctk.CTkFrame(
            self.content,
            fg_color=CARD_COLOR,
            corner_radius=15
        )
        form.pack(pady=20, padx=20)

        self.enrollment_entry = ctk.CTkEntry(
            form,
            width=300,
            height=45,
            placeholder_text="6-digit Enrollment Number"
        )
        self.enrollment_entry.pack(pady=15, padx=30)

        self.name_entry = ctk.CTkEntry(
            form,
            width=300,
            height=45,
            placeholder_text="Student Name"
        )
        self.name_entry.pack(pady=15)

        ctk.CTkButton(
            form,
            text="Capture Face",
            width=300,
            height=45,
            fg_color=SUCCESS_COLOR,
            hover_color="#15803D",
            command=self.capture_student
        ).pack(pady=20)

    def capture_student(self):
        enrollment = self.enrollment_entry.get().strip()
        name = self.name_entry.get().strip()

        if not enrollment or not name:
            messagebox.showerror("Error", "Please fill all fields")
            return

        success = capture_student_face(enrollment, name)

        if success:
            train_success = train_face_model()

            self.enrollment_entry.delete(0, "end")
            self.name_entry.delete(0, "end")

            if train_success:
                messagebox.showinfo(
                    "Success",
                    "Student registered and model trained successfully"
                )
                self.load_home()

    # ------------------------
    # TRAIN
    # ------------------------
    def train_model(self):
        success = train_face_model()

        if success:
            messagebox.showinfo(
                "Success",
                "Face model trained successfully"
            )
            self.load_home()

    # ------------------------
    # ATTENDANCE
    # ------------------------
    def take_attendance(self):
        self.clear_content()

        top_bar = ctk.CTkFrame(self.content, fg_color=BG_COLOR)
        top_bar.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            top_bar,
            text="Take Attendance",
            font=("Arial", 28, "bold"),
            text_color=TEXT_COLOR
        ).pack(side="left", padx=10)

        self.create_back_button(top_bar)

        attendance_frame = ctk.CTkFrame(
            self.content,
            fg_color=CARD_COLOR,
            corner_radius=15
        )
        attendance_frame.pack(pady=30, padx=30)

        for subject in SUBJECTS:
            ctk.CTkButton(
                attendance_frame,
                text=subject,
                width=250,
                height=45,
                fg_color=ACCENT_COLOR,
                hover_color="#3730A3",
                command=lambda sub=subject: start_attendance(sub)
            ).pack(pady=10)

    # ------------------------
    # REPORTS
    # ------------------------
    def show_reports(self):
        dialog = ctk.CTkInputDialog(
            text="Enter Admin Password",
            title="Access Reports"
        )

        password = dialog.get_input()

        if password is None:
            return

        if password.strip() != ADMIN_PASSWORD:
            messagebox.showerror("Access Denied", "Incorrect Password")
            return

        self.clear_content()
        load_reports_ui(self.content, back_callback=self.load_home)

    # ------------------------
    # LOGOUT
    # ------------------------
    def logout(self):
        confirm = messagebox.askyesno(
            "Logout",
            "Are you sure you want to logout?"
        )

        if confirm:
            self.frame.destroy()
            from login import LoginPage
            LoginPage(self.root)