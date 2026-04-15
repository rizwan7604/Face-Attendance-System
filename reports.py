import os
import shutil
import pandas as pd
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
from config import *
from train_image import train_face_model
from datetime import datetime

# ====================================================================================================
# GLOBAL ANALYTICS HELPERS (Updated to show ALL students)
# ====================================================================================================
def calculate_attendance_stats():
    import os
    import pandas as pd
    from config import ATTENDANCE_PATH, MASTER_DATA_PATH

    # 1. Load Master Data (This ensures ALL students are listed)
    if not os.path.exists(MASTER_DATA_PATH):
        return [], 0
    
    m_df = pd.read_csv(MASTER_DATA_PATH)
    m_df.columns = m_df.columns.str.strip().str.capitalize()
    
    # 2. Count total classes and student attendance
    total_classes = 0
    attendance_counts = {}

    if os.path.exists(ATTENDANCE_PATH):
        for root, dirs, files in os.walk(ATTENDANCE_PATH):
            for file in files:
                if file.endswith(".csv"):
                    total_classes += 1
                    try:
                        df = pd.read_csv(os.path.join(root, file))
                        df.columns = df.columns.str.strip().str.capitalize()
                        if "Enrollment" in df.columns:
                            # Use unique IDs per session to prevent double counting in one file
                            present_ids = df["Enrollment"].astype(str).unique()
                            for eid in present_ids:
                                attendance_counts[eid] = attendance_counts.get(eid, 0) + 1
                    except:
                        continue

    # 3. Create stats list by iterating through Master List
    stats = []
    for _, row in m_df.iterrows():
        eid = str(row.get("Enrollment", "")).strip()
        name = str(row.get("Name", "Unknown")).strip()
        count = attendance_counts.get(eid, 0)
        percent = round((count / total_classes) * 100, 2) if total_classes > 0 else 0
        stats.append((eid, name, count, percent))

    return stats, total_classes

# ====================================================================================================
# MAIN UI LOADER
# ====================================================================================================
def load_reports_ui(parent, back_callback=None):
    for widget in parent.winfo_children():
        widget.destroy()

    # ---------------------------------------------------------
    # UI STYLING & RESETTERS
    # ---------------------------------------------------------
    def configure_tree_style():
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#111827", foreground="white", fieldbackground="#111827", rowheight=36, font=("Arial", 12))
        style.configure("Treeview.Heading", font=("Arial", 13, "bold"), padding=8)
        style.map("Treeview", background=[("selected", "#4F46E5")])

    def clear_tree(tree):
        for item in tree.get_children(): tree.delete(item)

    def make_summary_card(parent_frame, title, value, color=TEXT_COLOR):
        card = ctk.CTkFrame(parent_frame, fg_color=CARD_COLOR, corner_radius=14, height=92)
        card.pack(fill="x", padx=8, pady=6); card.pack_propagate(False)
        ctk.CTkLabel(card, text=title, font=("Arial", 13, "bold"), text_color=SECONDARY_TEXT).pack(pady=(14, 4))
        ctk.CTkLabel(card, text=str(value), font=("Arial", 20, "bold"), text_color=color).pack(pady=(0, 8))

    def update_master_summary(total, reg, pend):
        for w in master_summary_frame.winfo_children(): w.destroy()
        ctk.CTkLabel(master_summary_frame, text="Final Summary", font=("Arial", 20, "bold"), text_color=TEXT_COLOR).pack(pady=(8, 10))
        make_summary_card(master_summary_frame, "Total Students", total)
        make_summary_card(master_summary_frame, "Registered", reg, SUCCESS_COLOR)
        make_summary_card(master_summary_frame, "Pending", pend, DANGER_COLOR)

    def update_reports_summary(rows):
        for w in reports_summary_frame.winfo_children(): w.destroy()
        ctk.CTkLabel(reports_summary_frame, text="Final Summary", font=("Arial", 20, "bold"), text_color=TEXT_COLOR).pack(pady=(8, 10))
        make_summary_card(reports_summary_frame, "Total Records", len(rows))
        u_ids = len(set(r["Enrollment"] for r in rows)) if rows else 0
        make_summary_card(reports_summary_frame, "Unique Students", u_ids, SUCCESS_COLOR)

    def update_daily_summary(total, p, a):
        for w in d_sum_f.winfo_children(): w.destroy()
        ctk.CTkLabel(d_sum_f, text="Final Summary", font=("Arial", 20, "bold"), text_color=TEXT_COLOR).pack(pady=(8, 10))
        make_summary_card(d_sum_f, "Total Students", total)
        make_summary_card(d_sum_f, "Present", p, SUCCESS_COLOR)
        make_summary_card(d_sum_f, "Absent", a, DANGER_COLOR)

    def update_subject_summary(total, p, a):
        for w in s_sum_f.winfo_children(): w.destroy()
        ctk.CTkLabel(s_sum_f, text="Final Summary", font=("Arial", 20, "bold"), text_color=TEXT_COLOR).pack(pady=(8, 10))
        make_summary_card(s_sum_f, "Total Students", total)
        make_summary_card(s_sum_f, "Present", p, SUCCESS_COLOR)
        make_summary_card(s_sum_f, "Absent", a, DANGER_COLOR)

    # ---------------------------------------------------------
    # DATA HANDLERS
    # ---------------------------------------------------------
    def get_master_df():
        if not os.path.exists(MASTER_DATA_PATH): return pd.DataFrame(columns=["Enrollment", "Name"])
        df = pd.read_csv(MASTER_DATA_PATH); df.columns = df.columns.str.strip()
        return df

    def get_all_attendance_rows():
        all_data = []
        if not os.path.exists(ATTENDANCE_PATH): return []
        for root, dirs, files in os.walk(ATTENDANCE_PATH):
            for file in files:
                if file.endswith(".csv"):
                    try:
                        df = pd.read_csv(os.path.join(root, file))
                        headers = {c.lower().strip(): c for c in df.columns}
                        for _, row in df.iterrows():
                            all_data.append({
                                "Enrollment": str(row.get(headers.get('enrollment'), "N/A")).strip(),
                                "Name": str(row.get(headers.get('name'), "N/A")).strip(),
                                "Subject": str(row.get(headers.get('subject'), "N/A")).strip(),
                                "Date": str(row.get(headers.get('date'), "N/A")).strip(),
                                "Time": str(row.get(headers.get('time'), "N/A")).strip(),
                                "Emotion": str(row.get(headers.get('emotion'), "Neutral")).strip()
                            })
                    except: continue
        return all_data

    configure_tree_style()

    # --- Header ---
    header_frame = ctk.CTkFrame(parent, fg_color=BG_COLOR); header_frame.pack(fill="x", padx=20, pady=(12, 6))
    ctk.CTkLabel(header_frame, text="Reports & Master Data", font=("Arial", 30, "bold"), text_color=TEXT_COLOR).pack(side="left", padx=10)
    if back_callback: ctk.CTkButton(header_frame, text="Back", width=110, height=40, fg_color=ACCENT_COLOR, command=back_callback).pack(side="right", padx=10)

    tabview = ctk.CTkTabview(parent, width=1100, height=600); tabview.pack(fill="both", expand=True, padx=20, pady=10)
    tab_master = tabview.add("Master Data")
    tab_reports = tabview.add("All Reports")
    tab_daily = tabview.add("Daily View")
    tab_subject = tabview.add("Subject View")
    tab_analytics = tabview.add("Analytics")

    # =========================================================
    # TAB 1: MASTER DATA
    # =========================================================
    m_top = ctk.CTkFrame(tab_master, fg_color=BG_COLOR); m_top.pack(fill="x", padx=12, pady=8)
    search_ent = ctk.CTkEntry(m_top, width=250, placeholder_text="Enrollment or Name"); search_ent.pack(side="left", padx=5)
    en_ent = ctk.CTkEntry(m_top, width=150, placeholder_text="ER (6-digit)"); en_ent.pack(side="left", padx=5)
    nm_ent = ctk.CTkEntry(m_top, width=200, placeholder_text="Full Name"); nm_ent.pack(side="left", padx=5)

    m_btns = ctk.CTkFrame(tab_master, fg_color=BG_COLOR); m_btns.pack(fill="x", padx=12, pady=5)
    m_content = ctk.CTkFrame(tab_master, fg_color=BG_COLOR); m_content.pack(fill="both", expand=True, padx=12, pady=8)
    master_tree = ttk.Treeview(ctk.CTkFrame(m_content, fg_color=CARD_COLOR, corner_radius=15), columns=("Enrollment", "Name", "Status"), show="headings", height=16)
    master_tree.master.pack(side="left", fill="both", expand=True, padx=(0, 10)); master_tree.pack(fill="both", expand=True, padx=18, pady=18)
    for c in ("Enrollment", "Name", "Status"): master_tree.heading(c, text=c); master_tree.column(c, width=180, anchor="center")
    master_summary_frame = ctk.CTkFrame(m_content, fg_color=BG_COLOR, width=260); master_summary_frame.pack(side="right", fill="both", expand=False); master_summary_frame.pack_propagate(False)

    def load_master_data():
        clear_tree(master_tree); df = get_master_df().sort_values(by="Enrollment", key=lambda x: x.astype(int))
        reg_ids = set()
        if os.path.exists(STUDENT_DETAILS_PATH):
            rdf = pd.read_csv(STUDENT_DETAILS_PATH); reg_ids = set(rdf["Enrollment"].astype(str))
        for _, r in df.iterrows():
            st = "Registered" if str(r["Enrollment"]) in reg_ids else "Not Registered"
            master_tree.insert("", "end", values=(r["Enrollment"], r["Name"], st))
        update_master_summary(len(df), len(reg_ids), len(df)-len(reg_ids))

    def bulk_import():
        f = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if f:
            df = pd.read_csv(f); df.columns = df.columns.str.strip()
            if messagebox.askyesno("Batch Import", "Replace list and wipe all history?"):
                if os.path.exists(ATTENDANCE_PATH): shutil.rmtree(ATTENDANCE_PATH); os.makedirs(ATTENDANCE_PATH)
                if os.path.exists(TRAINING_IMAGE_PATH): shutil.rmtree(TRAINING_IMAGE_PATH); os.makedirs(TRAINING_IMAGE_PATH)
                if os.path.exists(STUDENT_DETAILS_PATH): os.remove(STUDENT_DETAILS_PATH)
                df[["Enrollment", "Name"]].to_csv(MASTER_DATA_PATH, index=False)
                load_master_data(); clear_tree(report_tree); messagebox.showinfo("Success", "Import Successful.")

    ctk.CTkButton(m_btns, text="Search", width=110, command=load_master_data).pack(side="left", padx=5)
    ctk.CTkButton(m_btns, text="Load All", width=110, fg_color=SUCCESS_COLOR, command=load_master_data).pack(side="left", padx=5)
    ctk.CTkButton(m_btns, text="Import CSV", width=110, fg_color="#F59E0B", text_color="black", command=bulk_import).pack(side="left", padx=5)
    ctk.CTkButton(m_btns, text="Add", width=110, fg_color=WARNING_COLOR, text_color="black", command=load_master_data).pack(side="left", padx=5)
    ctk.CTkButton(m_btns, text="Delete", width=110, fg_color=DANGER_COLOR, command=load_master_data).pack(side="left", padx=5)

    # =========================================================
    # TAB 2: ALL REPORTS
    # =========================================================
    rep_content = ctk.CTkFrame(tab_reports, fg_color=BG_COLOR); rep_content.pack(fill="both", expand=True, padx=12, pady=8)
    report_tree = ttk.Treeview(ctk.CTkFrame(rep_content, fg_color=CARD_COLOR, corner_radius=15), columns=("Enrollment", "Name", "Subject", "Date", "Time", "Emotion"), show="headings", height=16)
    report_tree.master.pack(side="left", fill="both", expand=True, padx=(0, 10)); report_tree.pack(fill="both", expand=True, padx=18, pady=18)
    for c in ("Enrollment", "Name", "Subject", "Date", "Time", "Emotion"): report_tree.heading(c, text=c); report_tree.column(c, width=110, anchor="center")
    reports_summary_frame = ctk.CTkFrame(rep_content, fg_color=BG_COLOR, width=260); reports_summary_frame.pack(side="right", fill="both", expand=False); reports_summary_frame.pack_propagate(False)

    def load_all_reports():
        rows = get_all_attendance_rows(); clear_tree(report_tree)
        for r in rows: report_tree.insert("", "end", values=(r["Enrollment"], r["Name"], r["Subject"], r["Date"], r["Time"], r["Emotion"]))
        update_reports_summary(rows)

    ctk.CTkButton(tab_reports, text="Refresh Logs", width=200, command=load_all_reports).pack(pady=5)

    # =========================================================
    # TAB 3 & 4: DAILY & SUBJECT VIEWS
    # =========================================================
    d_top = ctk.CTkFrame(tab_daily, fg_color=BG_COLOR); d_top.pack(fill="x", padx=12, pady=8)
    d_content = ctk.CTkFrame(tab_daily, fg_color=BG_COLOR); d_content.pack(fill="both", expand=True, padx=12, pady=8)
    daily_tree = ttk.Treeview(ctk.CTkFrame(d_content, fg_color=CARD_COLOR, corner_radius=15), columns=("Enrollment", "Name", "Status"), show="headings", height=16)
    daily_tree.master.pack(side="left", fill="both", expand=True, padx=(0, 10)); daily_tree.pack(fill="both", expand=True, padx=18, pady=18)
    for c in ("Enrollment", "Name", "Status"): daily_tree.heading(c, text=c); daily_tree.column(c, width=180, anchor="center")
    d_sum_f = ctk.CTkFrame(d_content, width=260); d_sum_f.pack(side="right", fill="both", expand=False); d_sum_f.pack_propagate(False)

    def load_daily_view():
        clear_tree(daily_tree); date = daily_date_var.get(); m_df = get_master_df()
        if not date: return
        p_ids = {r["Enrollment"] for r in get_all_attendance_rows() if r["Date"] == date}
        pc, ac = 0, 0
        for _, r in m_df.iterrows():
            is_p = str(r["Enrollment"]) in p_ids
            daily_tree.insert("", "end", values=(r["Enrollment"], r["Name"], "Present" if is_p else "Absent"))
            if is_p: pc += 1 
            else: ac += 1
        update_daily_summary(len(m_df), pc, ac)

    dates = sorted(list(set(r["Date"] for r in get_all_attendance_rows())), reverse=True)
    daily_date_var = ctk.StringVar(value=dates[0] if dates else "")
    ctk.CTkOptionMenu(d_top, values=dates if dates else [""], variable=daily_date_var, width=200).pack(side="left", padx=10)
    ctk.CTkButton(d_top, text="Load Data", width=150, fg_color=ACCENT_COLOR, command=load_daily_view).pack(side="left", padx=10)

    s_top = ctk.CTkFrame(tab_subject, fg_color=BG_COLOR); s_top.pack(fill="x", padx=12, pady=8)
    s_content = ctk.CTkFrame(tab_subject, fg_color=BG_COLOR); s_content.pack(fill="both", expand=True, padx=12, pady=8)
    subject_tree = ttk.Treeview(ctk.CTkFrame(s_content, fg_color=CARD_COLOR, corner_radius=15), columns=("Enrollment", "Name", "Status"), show="headings", height=16)
    subject_tree.master.pack(side="left", fill="both", expand=True, padx=(0, 10)); subject_tree.pack(fill="both", expand=True, padx=18, pady=18)
    for c in ("Enrollment", "Name", "Status"): subject_tree.heading(c, text=c); subject_tree.column(c, width=180, anchor="center")
    s_sum_f = ctk.CTkFrame(s_content, width=260); s_sum_f.pack(side="right", fill="both", expand=False); s_sum_f.pack_propagate(False)

    def load_subject_view():
        clear_tree(subject_tree); sub = sub_var.get(); m_df = get_master_df()
        if not sub: return
        p_ids = {r["Enrollment"] for r in get_all_attendance_rows() if r["Subject"] == sub}
        pc, ac = 0, 0
        for _, r in m_df.iterrows():
            is_p = str(r["Enrollment"]) in p_ids
            subject_tree.insert("", "end", values=(r["Enrollment"], r["Name"], "Present" if is_p else "Absent"))
            if is_p: pc += 1 
            else: ac += 1
        update_subject_summary(len(m_df), pc, ac)

    subs = sorted(list(set(r["Subject"] for r in get_all_attendance_rows())))
    sub_var = ctk.StringVar(value=subs[0] if subs else "")
    ctk.CTkOptionMenu(s_top, values=subs if subs else [""], variable=sub_var, width=200).pack(side="left", padx=10)
    ctk.CTkButton(s_top, text="Load Data", width=150, fg_color=ACCENT_COLOR, command=load_subject_view).pack(side="left", padx=10)

    # =========================================================
    # TAB 5: ANALYTICS (FIXED: NOW SHOWS ALL MASTER STUDENTS)
    # =========================================================
    an_content = ctk.CTkFrame(tab_analytics, fg_color=BG_COLOR); an_content.pack(fill="both", expand=True, padx=12, pady=8)
    an_tree = ttk.Treeview(ctk.CTkFrame(an_content, fg_color=CARD_COLOR, corner_radius=15), columns=("Enrollment", "Name", "Attended", "Percentage"), show="headings", height=16)
    an_tree.master.pack(side="left", fill="both", expand=True, padx=(0, 10)); an_tree.pack(fill="both", expand=True, padx=18, pady=18)
    for c in ("Enrollment", "Name", "Attended", "Percentage"): an_tree.heading(c, text=c); an_tree.column(c, width=140, anchor="center")
    an_sum_f = ctk.CTkFrame(an_content, width=280); an_sum_f.pack(side="right", fill="both", expand=False); an_sum_f.pack_propagate(False)

    def load_analytics():
        clear_tree(an_tree); [w.destroy() for w in an_sum_f.winfo_children()]
        stats, tc = calculate_attendance_stats(); topper = ("-", 0)
        
        subj_counts = {}
        if os.path.exists(ATTENDANCE_PATH):
            for root, dirs, files in os.walk(ATTENDANCE_PATH):
                for file in files:
                    if file.endswith(".csv"):
                        try:
                            df = pd.read_csv(os.path.join(root, file))
                            if not df.empty:
                                s_name = str(df.iloc[0].get("Subject", "Unknown")).strip()
                                subj_counts[s_name] = subj_counts.get(s_name, 0) + 1
                        except: continue

        # stats now contains EVERY student from the master list
        for e, n, count, p in stats:
            an_tree.insert("", "end", values=(e, n, count, f"{p}%"))
            if p > topper[1]: topper = (n, p)

        ctk.CTkLabel(an_sum_f, text="Performance", font=("Arial", 20, "bold"), text_color=TEXT_COLOR).pack(pady=10)
        make_summary_card(an_sum_f, "Total Sessions", tc)
        
        ctk.CTkLabel(an_sum_f, text="Classes Per Subject:", font=("Arial", 14, "bold"), text_color=ACCENT_COLOR).pack(anchor="w", padx=15, pady=(10, 5))
        for s, c in sorted(subj_counts.items()):
            ctk.CTkLabel(an_sum_f, text=f"• {s}: {c}", font=("Arial", 13), text_color=TEXT_COLOR).pack(anchor="w", padx=25)

        ctk.CTkLabel(an_sum_f, text=f"Top Student: {topper[0]} ({topper[1]}%)", font=("Arial", 14, "bold"), text_color=SUCCESS_COLOR).pack(pady=20)

    ctk.CTkButton(tab_analytics, text="Refresh Analytics", width=200, command=load_analytics).pack(pady=10)

    # Initial Load
    load_master_data(); load_all_reports(); load_analytics()