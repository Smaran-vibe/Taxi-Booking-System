# main.py
import customtkinter as ctk
from tkinter import messagebox
import subprocess
import passenger_panel as passenger
import driver_dashboard
import sqlite3


from database import login_user, DB_NAME, register_admin


def open_roles():
    root.destroy()
    subprocess.Popen(["python", "roles.py"])


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("Gharjau Login")
root.geometry("900x600")
root.resizable(False, False)

left_frame = ctk.CTkFrame(root, width=450, height=600,
                          fg_color="#DAF072", corner_radius=0)
left_frame.pack(side="left", fill="both")

ghar_label = ctk.CTkLabel(left_frame, text="🚖Ghar",
                          font=("Arial", 28, "bold"),
                          text_color="#F4C400")
ghar_label.place(x=70, y=120)

jau_label = ctk.CTkLabel(left_frame, text="jau",
                         font=("Arial", 28, "bold"),
                         text_color="#000000")
jau_label.place(x=170, y=120)

tagline = ctk.CTkLabel(left_frame, text="Where You Go,\nWe Follow", font=(
    "Arial", 32, "bold"), text_color="black")
tagline.place(x=50, y=170)

desc = ctk.CTkLabel(left_frame, text="Book your taxi in seconds. Fast, reliable,\nand always available when you need us.",
                    font=("Arial", 14), text_color="black")
desc.place(x=40, y=260)

stats = ctk.CTkLabel(left_frame, text="24/7 Available     Happy Riders    7+ Cities",
                     font=("Arial", 14, "bold"), text_color="black")
stats.place(x=40, y=320)

right_frame = ctk.CTkFrame(root, width=450, height=600,
                           fg_color="white", corner_radius=0)
right_frame.pack(side="right", fill="both")

login_card = ctk.CTkFrame(right_frame, width=350,
                          height=400, fg_color="white", corner_radius=15)
login_card.place(relx=0.5, rely=0.5, anchor="center")

title_label = ctk.CTkLabel(login_card, text="Welcome Back", font=(
    "Arial", 28, "bold"), text_color="black")
title_label.pack(pady=(30, 10))

subtitle_label = ctk.CTkLabel(
    login_card, text="Sign in to continue booking", font=("Arial", 14), text_color="gray")
subtitle_label.pack(pady=(0, 20))

email_entry = ctk.CTkEntry(
    login_card, placeholder_text="you@example.com", width=280, height=40, corner_radius=8)
email_entry.pack(pady=10)

password_entry = ctk.CTkEntry(
    login_card, placeholder_text="Password", show="*", width=280, height=40, corner_radius=8)
password_entry.pack(pady=10)

remember_var = ctk.BooleanVar()
remember_check = ctk.CTkCheckBox(
    login_card, text="Remember me", variable=remember_var)
remember_check.pack(anchor="w", padx=5, pady=10)


def login():
    username_or_email = email_entry.get().strip()
    password = password_entry.get().strip()

    if username_or_email == "" or password == "":
        messagebox.showwarning("Input Error", "Please fill in all fields.")
        return

    try:
        result = login_user(username_or_email, password)
    except Exception as e:
        messagebox.showerror("Error", f"Login failure: {e}")
        return

    if result:
        role, user_data = result
        user_id = user_data[0]

        root.destroy()

        if role == "Admin":
            messagebox.showinfo("Login Success", "Welcome Admin!")
            subprocess.Popen(["python", "admin_dashboard.py"])
            return

        if role == "Passenger":
            messagebox.showinfo("Login Success", "Welcome Passenger!")
            passenger.start(user_id)
            return

        if role == "Driver":
            messagebox.showinfo("Login Success", "Welcome Driver!")
            driver_dashboard.start(user_id)
            return

        else:
            messagebox.showerror(
                "Unknown Role", f"No dashboard found for role: {role}")
            return

    else:
        messagebox.showerror(
            "Login Failed", "Invalid username/email or password.")


login_btn = ctk.CTkButton(login_card, text="Sign In", width=280, height=40, corner_radius=8,
                          fg_color="#DCF10F", text_color="black", hover_color="#BBE40A", command=login)
login_btn.pack(pady=20)

signup_label = ctk.CTkLabel(login_card, text="Don't have an account? Sign Up", font=("Arial", 12),
                            text_color="blue", cursor="hand2")
signup_label.pack()
signup_label.bind("<Button-1>", lambda e: open_roles())

root.mainloop()
