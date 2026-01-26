# rating_window.py
import tkinter as tk
from tkinter import ttk, messagebox
from database import submit_driver_rating


class RatingWindow(tk.Toplevel):
    def __init__(self, parent, ride_id):
        super().__init__(parent)

        self.ride_id = ride_id
        self.title("Rate Your Driver")
        self.geometry("300x240")
        self.resizable(False, False)

        ttk.Label(self, text="Rate Your Driver", font=("Arial", 14, "bold")).pack(pady=10)

        # Rating label
        ttk.Label(self, text="Give Rating (1–5):").pack(pady=5)

        # Rating dropdown
        self.rating_var = tk.IntVar(value=5)
        self.rating_box = ttk.Combobox(
            self, values=[1, 2, 3, 4, 5],
            state="readonly",
            textvariable=self.rating_var
        )
        self.rating_box.pack(pady=5)

        # Submit button
        ttk.Button(self, text="Submit Rating", command=self.submit_rating).pack(pady=15)

    def submit_rating(self):
        rating = self.rating_var.get()

        success = submit_driver_rating(self.ride_id, rating)

        if success:
            messagebox.showinfo("Thank You!", "Your rating has been submitted.")
            self.destroy()
        else:
            messagebox.showerror("Error", "Failed to submit rating.")
