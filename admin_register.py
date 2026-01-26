import customtkinter as ctk
from tkinter import messagebox
import subprocess
from database import register_admin, create_tables

create_tables()


def open_main():
    root.destroy()
    subprocess.Popen(["python", "main.py"])


# Appearance and theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Main Window
root = ctk.CTk()
root.title("Admin Panel")
root.geometry("700x600")
root.resizable(False, False)

# Main Frame
main_frame = ctk.CTkFrame(root, width=600, height=500,
                          fg_color="#1e1e1e", corner_radius=20)
main_frame.place(relx=0.5, rely=0.5, anchor="center")

# Title
title_label = ctk.CTkLabel(main_frame, text="Log In", font=(
    "Arial", 20, "bold"), text_color="white")
title_label.pack(pady=(10, 5), anchor="w", padx=30)


subtitle_label = ctk.CTkLabel(
    main_frame, text="For admin access", font=("Arial", 14), text_color="#bfbfbf")
subtitle_label.pack(pady=(0, 20), anchor="w", padx=30)

# INPUT FIELDS
user_name_entry = ctk.CTkEntry(
    main_frame, placeholder_text="Username", width=300, height=40, corner_radius=8)
user_name_entry.pack(pady=10)

password_entry = ctk.CTkEntry(
    main_frame, placeholder_text="Password", show="*", width=300, height=40, corner_radius=8)
password_entry.pack(pady=10)

confirm_entry = ctk.CTkEntry(main_frame, placeholder_text="Confirm password",
                             show="*", width=300, height=40, corner_radius=8)
confirm_entry.pack(pady=10)


def signup():
    username = user_name_entry.get()
    password = password_entry.get()
    confirm_password = confirm_entry.get()

    if not username or not password or not confirm_password:
        messagebox.showwarning("Input Error", "Please fill in all fields.")
        return

    # Password match check
    if password != confirm_password:
        messagebox.showerror("Error", "Passwords do not match!")
        return

    # Try to register admin user in DB
    result = register_admin(username, password)

    if result == "exists":
        messagebox.showerror("Error", "An admin account already exists!.")
        return

    if result is True:
        messagebox.showinfo("Success", "Admin account created successfully!")
        open_main()
        return

    messagebox.showerror(
        "Error", "Failed to create admin account. Username may be taken.")


#  BUTTON
signup_btn = ctk.CTkButton(
    main_frame, text="Sign up", width=300, height=40,
    corner_radius=8, fg_color="white", text_color="black",
    hover_color="#cdccc8", command=signup
)
signup_btn.pack(pady=20)

# Footer  label
footer_label = ctk.CTkLabel(main_frame, text="Back to login", font=("Arial", 12),
                            text_color="blue", cursor="hand2")
footer_label.pack(pady=10)

footer_label.bind("<Button-1>", lambda e: open_main())

root.mainloop()
