import customtkinter as ctk
from tkinter import messagebox
from config import *
from dashboard import Dashboard

class LoginPage:
    def __init__(self, root):
        self.root = root

        # Remove old Enter binding before setting new one
        self.root.unbind("<Return>")

        # Main Container
        self.main_frame = ctk.CTkFrame(root, fg_color=BG_COLOR)
        self.main_frame.pack(fill="both", expand=True)

        # Left Side Blue Panel
        self.left_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=ACCENT_COLOR,
            corner_radius=0
        )
        self.left_frame.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            self.left_frame,
            text="Smart Attendance\nSystem",
            font=("Arial", 38, "bold"),
            text_color="white",
            justify="left"
        ).pack(pady=(180, 20), padx=40, anchor="w")

        ctk.CTkLabel(
            self.left_frame,
            text="AI Powered Face Recognition Attendance",
            font=("Arial", 18),
            text_color="white",
            justify="left"
        ).pack(padx=40, anchor="w")

        ctk.CTkLabel(
            self.left_frame,
            text="Fast • Secure • Modern",
            font=("Arial", 15, "bold"),
            text_color="#DBEAFE"
        ).pack(pady=(20, 0), padx=40, anchor="w")

        # Right Side
        self.right_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=BG_COLOR,
            corner_radius=0
        )
        self.right_frame.pack(side="right", fill="both", expand=True)

        self.login_card = ctk.CTkFrame(
            self.right_frame,
            width=420,
            height=500,
            fg_color=CARD_COLOR,
            corner_radius=20
        )
        self.login_card.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            self.login_card,
            text="Admin Login",
            font=("Arial", 30, "bold"),
            text_color=TEXT_COLOR
        ).pack(pady=(50, 10))

        ctk.CTkLabel(
            self.login_card,
            text="Enter your credentials to continue",
            font=("Arial", 14),
            text_color=SECONDARY_TEXT
        ).pack(pady=(0, 30))

        self.username_entry = ctk.CTkEntry(
            self.login_card,
            width=300,
            height=45,
            placeholder_text="Username",
            corner_radius=10
        )
        self.username_entry.pack(pady=15)

        self.password_entry = ctk.CTkEntry(
            self.login_card,
            width=300,
            height=45,
            placeholder_text="Password",
            show="*",
            corner_radius=10
        )
        self.password_entry.pack(pady=15)

        self.login_btn = ctk.CTkButton(
            self.login_card,
            text="Login",
            width=300,
            height=45,
            fg_color=ACCENT_COLOR,
            hover_color="#3730A3",
            corner_radius=10,
            font=("Arial", 15, "bold"),
            command=self.login
        )
        self.login_btn.pack(pady=30)

        ctk.CTkLabel(
            self.login_card,
            text="Only Admin Can Access",
            font=("Arial", 12),
            text_color=SECONDARY_TEXT
        ).pack()

        self.root.bind("<Return>", self.handle_enter)

        # Focus on username field at start
        self.username_entry.focus()

    def handle_enter(self, event):
        self.login()

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showwarning("Input Required", "Please enter username and password")
            return

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            self.root.unbind("<Return>")
            self.main_frame.destroy()
            Dashboard(self.root)
        else:
            self.password_entry.delete(0, "end")
            messagebox.showerror("Error", "Invalid Username or Password")