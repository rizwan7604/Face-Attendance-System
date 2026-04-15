import customtkinter as ctk
from login import LoginPage
from config import APP_NAME, WINDOW_SIZE, BG_COLOR

def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()
    app.title(APP_NAME)
    app.configure(fg_color=BG_COLOR)
    app.resizable(False, False)

    # Parse window size from config
    width, height = map(int, WINDOW_SIZE.split("x"))

    # Center window
    screen_width = app.winfo_screenwidth()
    screen_height = app.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2

    app.geometry(f"{width}x{height}+{x}+{y}")

    LoginPage(app)
    app.mainloop()

if __name__ == "__main__":
    main()