import customtkinter as ctk
from tkinter import messagebox
import subprocess
import sys
from geopy.geocoders import Nominatim

from database import (
    get_pending_rides_for_driver,
    driver_accept_ride,
    driver_reject_ride,
    complete_ride
)

geolocator = Nominatim(user_agent="gharjau_app")

# COORDS TO ADDRESS 
def looks_like_coords(s: str) -> bool:
    if not s or not isinstance(s, str):
        return False
    s_clean = s.strip().lstrip("(").rstrip(")")
    parts = [p.strip() for p in s_clean.split(",")]
    if len(parts) != 2:
        return False
    try:
        float(parts[0])
        float(parts[1])
        return True
    except ValueError:
        return False

def convert_coords_to_address(coord):
    try:
        if coord is None:
            return "Unknown"

        coord_str = str(coord).strip()

        if not looks_like_coords(coord_str):
            parts = coord_str.split(",")
            if len(parts) >= 2:
                return f"{parts[0].strip()}, {parts[1].strip()}"
            return coord_str

        s = coord_str.strip("()")
        lat, lon = [float(x) for x in s.split(",")]

        location = geolocator.reverse((lat, lon), language="en", timeout=10)
        if not location:
            return coord_str

        addr = location.raw.get("address", {})
        road = addr.get("road", "")
        suburb = addr.get("suburb", "")
        city = addr.get("city", addr.get("town", addr.get("village", "")))

        if road and city:
            return f"{road}, {city}"
        if suburb and city:
            return f"{suburb}, {city}"
        if city:
            return city

        return coord_str

    except Exception as e:
        print("Short address error:", e)
        return str(coord)


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


def logout(window=None):
    if window:
        try:
            window.destroy()
        except:
            pass
    subprocess.Popen(["python", "main.py"])

class DriverDashboard(ctk.CTk):
    def __init__(self, driver_id):
        super().__init__()
        self.driver_id = driver_id

        self.title("Driver Dashboard - Active Requests")
        self.geometry("600x750")
        self.resizable(False, False)

        self.active_ride_frame = None

        self._setup_ui()
        self._load_active_ride()
        self._load_requests()
    
    def _view_ratings(self):
        import sqlite3
        conn = sqlite3.connect("taxi_booking.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT r.rating, r.comment, rd.pickup, rd.destination
            FROM driver_ratings r
            JOIN rides rd ON r.ride_id = rd.id
            WHERE rd.driver_id = ?
        """, (self.driver_id,))

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            messagebox.showinfo("Ratings", "You have no ratings yet!")
            return

        text = ""
        for rating, comment, pu, de in rows:
            pu = convert_coords_to_address(pu)
            de = convert_coords_to_address(de)

            text += f"⭐ Rating: {rating}\n"
            text += f"💬 Comment: {comment}\n"
            text += f"📍 {pu} → {de}\n"
            text += "-" * 30 + "\n"

        messagebox.showinfo("Your Ratings", text)

    #  UI 
    def _setup_ui(self):
        hdr = ctk.CTkLabel(self, text="🚗 Driver Dashboard",
                           font=ctk.CTkFont(size=22, weight="bold"))
        hdr.pack(pady=(20, 10))

        self.status_label = ctk.CTkLabel(self, text="Loading requests...", text_color="yellow")
        self.status_label.pack(pady=(0, 10))

        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="Pending Rides",
                                                   width=400, height=460)
        self.scroll_frame.pack(padx=20, pady=5)
        self.scroll_frame.columnconfigure(0, weight=1)

        ctk.CTkButton(self, text="Refresh Requests",
                      command=self._reload_all).pack(pady=(10, 5))

        # NEW BUTTON 
        ctk.CTkButton(self, text="View Ratings",
                      fg_color="#7C4DFF",
                      command=self._view_ratings).pack(pady=5)

        ctk.CTkButton(self, text="Logout",
                      command=lambda: logout(self)).pack(pady=(5, 20))
        

    #  RELOAD 
    def _reload_all(self):
        self._load_active_ride()
        self._load_requests()
       



    def _load_active_ride(self):
        if self.active_ride_frame:
            self.active_ride_frame.destroy()

        ride = self._get_driver_active_ride()
        if not ride:
            return

        ride_id, pickup, destination, status, fare, sched_date, sched_time, assigned_by_admin = ride

        # Show admin assignment notification
        if assigned_by_admin == 1:
            messagebox.showinfo("Admin Assignment", "You have been assigned a ride by your admin")

        pickup = convert_coords_to_address(pickup)
        destination = convert_coords_to_address(destination)

        self.active_ride_frame = ctk.CTkFrame(self, fg_color="#333", corner_radius=12)
        self.active_ride_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(self.active_ride_frame,
                     text=f"🚕 Active Ride #{ride_id}",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color="white").pack(anchor="w", padx=15, pady=(10, 5))

        ctk.CTkLabel(self.active_ride_frame,
                     text=f"Pickup: {pickup}",
                     text_color="#FFF").pack(anchor="w", padx=15)

        ctk.CTkLabel(self.active_ride_frame,
                     text=f"Destination: {destination}",
                     text_color="#FFF").pack(anchor="w", padx=15)

        
        sched_time = sched_time if sched_time else None

        ctk.CTkLabel(self.active_ride_frame,
                     text=f"Date: {sched_date if sched_date else '-'} Time: {sched_time if sched_time else '-'}",
                     text_color="#FFF").pack(anchor="w", padx=15)

        ctk.CTkLabel(self.active_ride_frame,
                     text=f"Fare: Rs {fare:.2f}",
                     text_color="#00E676",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=5)

        ctk.CTkButton(self.active_ride_frame, text="Complete Ride",
                      fg_color="green",
                      command=lambda: self._handle_complete(ride_id)).pack(padx=15, pady=(10, 15))
        
   


    def _get_driver_active_ride(self):
        import sqlite3
        conn = sqlite3.connect("taxi_booking.db")
        cursor = conn.cursor()

        cursor.execute("SELECT current_ride_id FROM driver WHERE id=?", (self.driver_id,))
        row = cursor.fetchone()
        conn.close()

        if not row or not row[0]:
            return None

        ride_id = row[0]

        conn = sqlite3.connect("taxi_booking.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, pickup, destination, status, fare, scheduled_date, scheduled_time, assigned_by_admin
            FROM rides
            WHERE id=? AND status='Accepted'
        """, (ride_id,))
        ride = cursor.fetchone()
        conn.close()

        return ride

    def _handle_complete(self, ride_id):
        complete_ride(ride_id, self.driver_id)
        messagebox.showinfo("Completed", "Ride marked as completed!")
        self._reload_all()

    #  PENDING REQUESTS 
    def _load_requests(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        rides = get_pending_rides_for_driver(self.driver_id)

        if not rides:
            self.status_label.configure(text="✔ No Pending Requests", text_color="green")
            ctk.CTkLabel(self.scroll_frame, text="No new requests right now.").pack(pady=20)
            return

        self.status_label.configure(
            text=f"🔴 {len(rides)} Request(s) Pending",
            text_color="red"
        )

        for ride in rides:
            self._create_request_card(self.scroll_frame, ride)

    # REQUEST CARD 
    def _create_request_card(self, parent, ride):
        ride_id = ride[0]
        pickup = convert_coords_to_address(ride[2])
        destination = convert_coords_to_address(ride[3])

        fare = ride[4]
        status = ride[5]
        assigned_driver = ride[6]

        card = ctk.CTkFrame(parent, fg_color="#222831", corner_radius=12)
        card.pack(fill="x", padx=12, pady=12)

        ctk.CTkLabel(card, text=f"🚕 Ride #{ride_id}",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color="#FFD369").pack(anchor="w", padx=15, pady=(12, 5))

        ctk.CTkLabel(card, text=f"📍 Pickup: {pickup}",
                     text_color="#EEEEEE", wraplength=300).pack(anchor="w", padx=15)

        ctk.CTkLabel(card, text=f"🎯 Destination: {destination}",
                     text_color="#EEEEEE", wraplength=300).pack(anchor="w", padx=15)

        try:
            sched_date = ride[7] if len(ride) > 7 else None
            sched_time = ride[8] if len(ride) > 8 else None
        except Exception:
            sched_date = None
            sched_time = None
        ctk.CTkLabel(card, text=f"📅 {sched_date if sched_date else '-'} 🕒 {sched_time if sched_time else '-'}",
                     text_color="#EEEEEE", wraplength=300).pack(anchor="w", padx=15)

        ctk.CTkLabel(card, text=f"💸 Rs {fare:.2f}",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color="#00E676").pack(anchor="w", padx=15, pady=(8, 10))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=15, pady=(5, 12))

        if status == "Requested":
            ctk.CTkButton(btn_row, text="Accept", fg_color="#06D6A0",
                          command=lambda: self._handle_accept(ride_id)).pack(
                side="left", expand=True, fill="x", padx=5)

            ctk.CTkButton(btn_row, text="Reject", fg_color="#EF476F",
                          command=lambda: self._handle_reject(ride_id)).pack(
                side="left", expand=True, fill="x", padx=5)

        elif status == "Accepted" and assigned_driver == self.driver_id:
            ctk.CTkButton(btn_row, text="Complete Ride", fg_color="#118AB2",
                          hover_color="#0F6C8D",
                          command=lambda: self._handle_complete(ride_id)).pack(
                side="left", expand=True, fill="x", padx=5)

    # BUTTON HANDLERS 
    def _handle_accept(self, ride_id):
        result = driver_accept_ride(self.driver_id, ride_id)

        if result == "busy":
            messagebox.showerror("Busy", "You already have an active ride!")
            return

        messagebox.showinfo("Success", "Ride accepted!")
        self._reload_all()

    def _handle_reject(self, ride_id):
        driver_reject_ride(ride_id)
        messagebox.showinfo("Rejected", "Ride rejected!")
        self._reload_all()


#  START APP 
def start(driver_id):
    app = DriverDashboard(driver_id)
    app.mainloop()


if __name__ == "__main__":
    app = DriverDashboard(driver_id=1)
    app.mainloop()
