
import customtkinter as ctk

from passenger_dashboard_ui import PassengerDashboard

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

def start(user_id):
    """Entry function called after successful login."""
    app = PassengerDashboard(user_id)
    app.mainloop()

if __name__ == "__main__":
    print("Running Passenger Dashboard standalone")
    start(1)