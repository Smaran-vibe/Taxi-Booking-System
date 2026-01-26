import customtkinter as ctk
from tkinter import messagebox
import subprocess
import database
from database import register_driver, is_email_registered_elsewhere
import re


def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None


def open_main():
    root.destroy()
    subprocess.Popen(["python", "main.py"])


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title = ("Driver signup")
root.geometry("700x600")
root.resizable(False, False)

# main frame
main_frame = ctk.CTkFrame(root, width=600, height=500,
                          fg_color="black", corner_radius=20)
main_frame.place(relx=0.5, rely=0.5, anchor="center")

# Title
title_label = ctk.CTkLabel(main_frame, text=" Driver Sign up", font=(
    "Arial", 24, "bold"), text_color="#FED428")
title_label.pack(pady=(30, 20))

#  INPUT FIELDS

full_name_entry = ctk.CTkEntry(
    main_frame, placeholder_text="Full Name", width=300, height=40, corner_radius=8)
full_name_entry.pack(pady=10)

email_entry = ctk.CTkEntry(
    main_frame, placeholder_text="Email Address", width=300, height=40, corner_radius=8)
email_entry.pack(pady=10)

license_entry = ctk.CTkEntry(
    main_frame, placeholder_text="License no", width=300, height=40, corner_radius=8)
license_entry.pack(pady=10)

# Password and Confirm Password 

password_frame = ctk.CTkFrame(main_frame, fg_color="black")
password_frame.pack(pady=10)

password_entry = ctk.CTkEntry(
    password_frame, placeholder_text="Password", show="*", width=140, height=40)
password_entry.grid(row=0, column=0, padx=10)

confirm_entry = ctk.CTkEntry(
    password_frame, placeholder_text="Confirm Password", show="*", width=140, height=40)
confirm_entry.grid(row=0, column=1, padx=5)

#  CHECKBOX
agree_var = ctk.BooleanVar()
agree_check = ctk.CTkCheckBox(
    main_frame, text="I agree all statements in Terms of service", variable=agree_var)
agree_check.pack(pady=10)

#  SIGNUP BUTTON


def signup():
    name = full_name_entry.get().strip()
    email = email_entry.get().strip()
    password = password_entry.get().strip()
    license_number = license_entry.get().strip()
    confirm = confirm_entry.get().strip()

    
    if not name or not email or not password or not license_number or not confirm:
        messagebox.showwarning("Input Error", "Please fill in all fields.")
        return

    # EMAIL FORMAT VALIDATION
    if not is_valid_email(email):
        messagebox.showerror(
            "Invalid Email", "Please enter a valid email address.")
        return

    existing_role = is_email_registered_elsewhere(email, current_role="driver")
    if existing_role:
        messagebox.showerror(
            "Email Already Used",
            f"This email is already registered as a {existing_role}.\n"
            "Please use a different email."
        )
        return

    if password != confirm:
        messagebox.showerror("Error", "Passwords do not match!")
        return

    if not agree_var.get():
        messagebox.showwarning(
            "Agreement", "Please agree to the Terms of Service.")

    success = register_driver(
        name=name,
        email=email,
        password=password,
        license_number=license_number
    )

    if success:
        messagebox.showinfo("Success", f"Account created for {name}!")
        root.withdraw()
        subprocess.Popen(["python", "main.py"])
    else:
        messagebox.showerror(
            "Error", "Email or License Number already exists!")


signup_btn = ctk.CTkButton(main_frame, text="Sign up", width=300, height=40, corner_radius=8,
                           fg_color="#FED428", text_color="black", hover_color="#dcd395", command=signup)
signup_btn.pack(pady=20)

footer_label = ctk.CTkLabel(main_frame, text="Already have an account? Sign in", font=("Arial", 12),
                            text_color="blue", cursor="hand2")
footer_label.pack(pady=10)
footer_label.bind("<Button-1>", lambda e: open_main())
root.mainloop()
