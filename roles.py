import customtkinter as ctk
from tkinter import messagebox
import subprocess

def open_main():
    root.destroy()
    subprocess.Popen(["python", "main.py"])

def open_register():
    root.destroy()
    subprocess.Popen(["python","Passenger_register.py"])

def open_Driver_register():
    root.destroy()
    subprocess.Popen(["python","Driver_register.py"])

def open_admin_register():
    root.destroy()
    subprocess.Popen(["python","admin_register.py"])


# Appearance and theme
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

# Main Window
root = ctk.CTk()
root.title("Signup Page")
root.geometry("700x500")
root.resizable(False, False)

# Main Frame 
main_frame = ctk.CTkFrame(root, width=600, height=400, fg_color="white", corner_radius=15)
main_frame.place(relx=0.5, rely=0.5, anchor="center")

# Title
title_label = ctk.CTkLabel(main_frame, text="SELECT USER TYPE", font=("Arial", 24, "bold"), text_color="black")
title_label.pack(pady=(20, 10))


underline = ctk.CTkLabel(main_frame, text="__", font=("Arial", 24), text_color="#a020f0")  
underline.pack(pady=(0, 20))

# Variable to store selection
selected_role = ctk.StringVar(value="")

# Role Buttons (Cards)
def select_role(role):
    selected_role.set(role)
    messagebox.showinfo("Role Selected", f"You selected: {role}")

role_frame = ctk.CTkFrame(main_frame, fg_color="white")
role_frame.pack(pady=20)

DR_btn = ctk.CTkButton(role_frame, text="🚖 Driver", width=150, height=150, corner_radius=15,
                       fg_color="#f8f9fa", text_color="black", hover_color="#dcdcdc",
                       command=lambda: select_role("Driver"))
DR_btn.grid(row=0, column=0, padx=15)
DR_btn.bind ("<Button-1>",lambda e: open_Driver_register())

Pa_btn = ctk.CTkButton(role_frame, text="👤 Passenger", width=150, height=150, corner_radius=15,
                       fg_color="#f8f9fa", text_color="black", hover_color="#dcdcdc",
                       command=lambda: select_role("Passenger"))
Pa_btn.grid(row=0, column=1, padx=15)
Pa_btn.bind ("<Button-1>",lambda e: open_register())


ad_btn = ctk.CTkButton(role_frame, text="Admin", width=150, height=150, corner_radius=15,
                        fg_color="#a020f0", text_color="white", hover_color="#8b008b",
                        command=lambda: select_role("Admin"))
ad_btn.grid(row=0, column=2, padx=15)
ad_btn.bind("<Button-1>",lambda e: open_admin_register())

# Navigation Buttons
nav_frame = ctk.CTkFrame(main_frame, fg_color="white")
nav_frame.pack(pady=30)


back_btn = ctk.CTkButton(nav_frame, text="Back", width=100, corner_radius=20, fg_color="#f8f9fa", text_color="black")
back_btn.grid(row=0, column=0, padx=20)
back_btn.bind("<Button-1>", lambda e: open_main())

next_btn = ctk.CTkButton(nav_frame, text="→", width=60, corner_radius=30, fg_color="#a020f0", text_color="white")
next_btn.grid(row=0, column=1, padx=20)


root.mainloop()