import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import pandas as pd
import os

# Password Protected Panel
def teacher_panel_ui():
    # Password Check
    password = simpledialog.askstring("Admin Access", "Enter Teacher Password:", show='*')
    if password != "admin123":
        messagebox.showerror("Error", "Wrong Password!")
        return

    # Master Data Management Window
    panel = tk.Toplevel()
    panel.title("Master Data Manager")
    panel.geometry("500x400")
    panel.configure(background="#0B0E14")

    tk.Label(panel, text="MASTER DATA CONTROL", bg="#0B0E14", fg="#58A6FF", font=("Arial", 20, "bold")).pack(pady=30)

    def browse_and_upload():
        # File select karne ke liye
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            try:
                new_df = pd.read_csv(file_path)
                # Check columns
                if 'Enrollment' in new_df.columns and 'Name' in new_df.columns:
                    # Alphabetical Sort
                    new_df = new_df[['Enrollment', 'Name']].sort_values(by='Name')
                    
                    # Overwrite (Purani file apne aap delete hokar nayi ban jayegi)
                    save_path = "MasterData/student_list.csv"
                    os.makedirs("MasterData", exist_ok=True)
                    new_df.to_csv(save_path, index=False)
                    
                    messagebox.showinfo("Success", "Master List Successfully Replaced and Sorted!")
                    panel.destroy() # Upload ke baad window band
                else:
                    messagebox.showerror("Format Error", "CSV mein 'Enrollment' aur 'Name' columns hone chahiye!")
            except Exception as e:
                messagebox.showerror("Error", f"File upload nahi ho payi: {e}")

    # Main Button
    upload_btn = tk.Button(panel, text="BROWSE & REPLACE MASTER CSV", command=browse_and_upload, 
                           bg="#f59e0b", fg="black", font=("Arial", 12, "bold"), width=30, height=2)
    upload_btn.pack(pady=50)

    tk.Label(panel, text="Note: Nayi file upload karne par\npurana master data delete ho jayega.", 
             bg="#0B0E14", fg="gray").pack()