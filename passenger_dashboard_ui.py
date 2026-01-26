import customtkinter as ctk
import tkinter as tk
import tkintermapview
import requests
from geopy.geocoders import Nominatim
from tkinter import messagebox
from datetime import datetime, date, timedelta
from customtkinter import CTkLabel


from passenger_constants import (
    KATHMANDU_CENTER,
    INITIAL_ZOOM,
    haversine_km,
    logout,
    PRICE_NORMAL,
    PRICE_COMFORT
)
from geo_routing import GeoRoutingMixin
from booking_management import BookingManagementMixin

from database import get_active_ride, create_ride, cancel_ride, submit_driver_rating


ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class PassengerDashboard(ctk.CTk, GeoRoutingMixin, BookingManagementMixin):
    def __init__(self, passenger_id):
        super().__init__()

        if isinstance(passenger_id, tuple):
            passenger_id = passenger_id[0]
        self.user_id = int(passenger_id)

        # WINDOW & STATE
        self.title("Passenger Dashboard")
        self.geometry("850x700")
        self.minsize(600, 600)
        self.resizable(True, True)
        self.attributes('-fullscreen', False)

        self.from_loc, self.to_loc = None, None
        self.from_marker, self.to_marker = None, None
        self.current_path = None
        self.selecting_mode = None
        self.selected_card = "normal"
        self.rates = {"normal": PRICE_NORMAL, "comfort": PRICE_COMFORT}
        self.ride_info, self.ride_active = None, False
        self.current_ride_id = None
        self.geolocator = Nominatim(user_agent="taxi_booking_app_v1")

       
        self.current_driver_id = None
        self.rating_value = 0
        self.star_buttons = []

        try:
            GeoRoutingMixin.__init__(self)
        except Exception:
            pass
        try:
            BookingManagementMixin.__init__(self)
        except Exception:
            pass

        # Layout grid
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.map_card = ctk.CTkFrame(self, fg_color="#2b2b2b")
        self.map_card.grid(row=0, column=0, padx=(
            14, 7), pady=14, sticky="nsew")
        self.map_card.grid_rowconfigure(1, weight=1)
        self.map_card.grid_columnconfigure(0, weight=1)

        top_inputs = ctk.CTkFrame(self.map_card, fg_color="#343638")
        top_inputs.grid(row=0, column=0, padx=8, pady=8, sticky="ew")
        top_inputs.grid_columnconfigure((0, 1), weight=1)

        # From Input/Button Row
        self.input_from = ctk.CTkEntry(
            top_inputs, placeholder_text="Where from?")
        self.input_from.grid(row=0, column=0, padx=(
            10, 4), pady=(8, 4), sticky="ew")
        self.input_from.bind(
            "<FocusIn>", lambda e: self._set_selecting_mode("from"))
        self.input_from.bind(
            "<Return>", lambda e: self._search_location_from())

        ctk.CTkButton(
            top_inputs, text="Search", width=60,
            command=lambda: self._search_location_from()
        ).grid(row=0, column=1, padx=(0, 10), pady=(8, 4), sticky="w")

        # To Input/Button Row
        self.input_to = ctk.CTkEntry(
            top_inputs, placeholder_text="Where to?", placeholder_text_color="black")
        self.input_to.grid(row=1, column=0, padx=(
            10, 4), pady=(4, 8), sticky="ew")
        self.input_to.bind(
            "<FocusIn>", lambda e: self._set_selecting_mode("to"))
        self.input_to.bind("<Return>", lambda e: self._search_location_to())

        ctk.CTkButton(
            top_inputs, text="Search", width=60,
            command=lambda: self._search_location_to()
        ).grid(row=1, column=1, padx=(0, 10), pady=(4, 8), sticky="w")

        # Map widget
        self.map_widget = tkintermapview.TkinterMapView(
            self.map_card, corner_radius=10, max_zoom=20)
        try:
            self.map_widget.set_tile_server(
                "https://tile.openstreetmap.org/{z}/{x}/{y}.png")
        except Exception:
            pass
        self.map_widget.grid(row=1, column=0, padx=8, pady=8, sticky="nsew")
        self.map_widget.set_position(
            KATHMANDU_CENTER[0], KATHMANDU_CENTER[1], zoom=INITIAL_ZOOM)

        try:
            self.map_widget.add_right_click_menu_command(
                label="Set 'From' Here", command=self._set_from_on_map_click, pass_coords=True)
            self.map_widget.add_right_click_menu_command(
                label="Set 'To' Here", command=self._set_to_on_map_click, pass_coords=True)
        except Exception:
            pass

        self.hint_card = ctk.CTkFrame(
            self.map_card, fg_color="#343638", width=120, height=50)
        self.hint_card.place(relx=0.02, rely=0.22)
        self.lbl_distance_hint = ctk.CTkLabel(
            self.hint_card, text="Distance\n-- km", font=ctk.CTkFont(size=10, weight="bold"), text_color="white")
        self.lbl_distance_hint.pack(expand=True, padx=8, pady=6)

        #  RIGHT: Controls
        self.right_panel = ctk.CTkFrame(self, fg_color="#1f1f1f")
        self.right_panel.grid(row=0, column=1, padx=(
            7, 14), pady=14, sticky="nsew")
        self.right_panel.grid_columnconfigure(0, weight=1)
        for r in range(8):
            self.right_panel.grid_rowconfigure(r, weight=0)
        self.right_panel.grid_rowconfigure(7, weight=1)

        ctk.CTkButton(self.right_panel, text="Logout", fg_color="#4BEAFF", hover_color="#393A3B", text_color="black",
                      width=80, height=30, command=lambda: logout(self)).grid(row=0, column=0, sticky="ne", padx=10, pady=(10, 0))

        ctk.CTkLabel(self.right_panel, text="Choose Your Ride", font=ctk.CTkFont(size=16, weight="bold"),
                     anchor="w", text_color="white").grid(row=1, column=0, padx=10, pady=(10, 6), sticky="w")

        self.datetime_label = ctk.CTkLabel(
            self.right_panel,
            text=datetime.now().strftime("📅 %Y-%m-%d   ⏰ %H:%M %p"),
            font=ctk.CTkFont(size=12),
            text_color="white"
        )

        self.datetime_label.place(relx=0.98, rely=0.06, anchor="ne")
        self.update_time()

        # Cards frame
        cards_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        cards_frame.grid(row=2, column=0, padx=10, pady=(6, 8), sticky="ew")
        cards_frame.grid_columnconfigure(0, weight=1)

        # Normal card
        self.card_normal = ctk.CTkFrame(
            cards_frame, fg_color="#343638", cursor="hand2", height=85)
        self.card_normal.grid(row=0, column=0, padx=2,
                              pady=(0, 6), sticky="ew")
        self.card_normal.grid_propagate(False)
        self.card_normal.bind(
            "<Button-1>", lambda e: self._select_card("normal"))
        self.card_normal.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.card_normal, text="Normal", font=ctk.CTkFont(size=14, weight="bold"),
                     anchor="w", text_color="white").grid(row=0, column=0, padx=10, pady=(8, 0), sticky="w")
        ctk.CTkLabel(self.card_normal, text="Standard ride", anchor="w", text_color="white",
                     font=ctk.CTkFont(size=10)).grid(row=1, column=0, padx=10, sticky="w")
        self.n_price = ctk.CTkLabel(
            self.card_normal, text=f"Rs {PRICE_NORMAL:.0f}/km", font=ctk.CTkFont(size=12, weight="bold"), text_color="white")
        self.n_price.grid(row=2, column=0, padx=10, pady=(0, 8), sticky="w")

        # Comfort card
        self.card_comfort = ctk.CTkFrame(
            cards_frame, fg_color="#343638", cursor="hand2", height=85)
        self.card_comfort.grid(row=1, column=0, padx=2,
                               pady=(6, 0), sticky="ew")
        self.card_comfort.grid_propagate(False)
        self.card_comfort.bind(
            "<Button-1>", lambda e: self._select_card("comfort"))
        self.card_comfort.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.card_comfort, text="Comfort", font=ctk.CTkFont(size=14, weight="bold"),
                     anchor="w", text_color="white").grid(row=0, column=0, padx=10, pady=(8, 0), sticky="w")
        ctk.CTkLabel(self.card_comfort, text="Premium comfortable ride", anchor="w",
                     text_color="white", font=ctk.CTkFont(size=10)).grid(row=1, column=0, padx=10, sticky="w")
        self.c_price = ctk.CTkLabel(
            self.card_comfort, text=f"Rs {PRICE_COMFORT:.0f}/km", font=ctk.CTkFont(size=12, weight="bold"), text_color="white")
        self.c_price.grid(row=2, column=0, padx=10, pady=(0, 8), sticky="w")

        # Breakdown
        breakdown = ctk.CTkFrame(self.right_panel, fg_color="#2b2b2b")
        breakdown.grid(row=3, column=0, padx=10, pady=(6, 6), sticky="ew")
        breakdown.grid_columnconfigure(0, weight=1)

        self.lbl_distance = ctk.CTkLabel(
            breakdown, text="Distance: - km", anchor="w", font=ctk.CTkFont(size=11), text_color="white")
        self.lbl_distance.grid(row=0, column=0, padx=10,
                               pady=(10, 2), sticky="w")

        self.lbl_fare = ctk.CTkLabel(breakdown, text="Fare: Rs 0.00", anchor="w", font=ctk.CTkFont(
            size=14, weight="bold"), text_color="white")
        self.lbl_fare.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")

        schedule_frame = ctk.CTkFrame(breakdown, fg_color="transparent")
        schedule_frame.grid(row=2, column=0, padx=10,
                            pady=(0, 10), sticky="ew")
        schedule_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(schedule_frame, text="Date (YYYY-MM-DD)", text_color="white").grid(
            row=0, column=0, padx=(0, 8), pady=(0, 4), sticky="w")
        self.entry_date = ctk.CTkEntry(schedule_frame)
        self.entry_date.grid(row=0, column=1, padx=(0, 0),
                             pady=(0, 4), sticky="ew")

        ctk.CTkLabel(schedule_frame, text="Time (HH:MM)", text_color="white").grid(
            row=1, column=0, padx=(0, 8), pady=(0, 0), sticky="w")
        self.entry_time = ctk.CTkEntry(schedule_frame)
        self.entry_time.grid(row=1, column=1, padx=(0, 0),
                             pady=(0, 0), sticky="ew")

        # Book button
        self.book_btn = ctk.CTkButton(self.right_panel, text="Book Ride", fg_color="#00C48C",
                                      hover_color="#009f74", height=40, command=self._confirm_ride)
        self.book_btn.grid(row=4, column=0, padx=10, pady=(6, 6), sticky="ew")

        # Status frame
        self.status_frame = ctk.CTkFrame(self.right_panel, fg_color="#2b2b2b")
        self.status_frame.grid(row=5, column=0, padx=10,
                               pady=(8, 8), sticky="ew")
        self.status_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.status_frame, text="Ride Status", font=ctk.CTkFont(
            size=12, weight="bold"), text_color="white").grid(row=0, column=0, padx=8, pady=(6, 1), sticky="w")
        self.lbl_status_value = ctk.CTkLabel(
            self.status_frame, text="No ride booked", text_color="white", font=ctk.CTkFont(size=10))
        self.lbl_status_value.grid(
            row=1, column=0, padx=8, pady=(0, 6), sticky="w")

        self.btn_cancel_ride = ctk.CTkButton(
            self.status_frame, text="Cancel Ride", fg_color="#FF4C4C", hover_color="#D93636", height=30, command=self._cancel_ride)
        self.btn_cancel_ride.grid(
            row=2, column=0, padx=8, pady=(6, 8), sticky="ew")
        self.btn_cancel_ride.grid_remove()

        # Footer
        footer_frame = ctk.CTkFrame(
            self.right_panel, fg_color="#003B7A", height=90)
        footer_frame.grid(row=6, column=0, padx=10, pady=(6, 10), sticky="ew")
        footer_frame.grid_columnconfigure(0, weight=0)
        footer_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(footer_frame, text="👤", width=40, height=40, fg_color="#0059B3", corner_radius=20, font=(
            "Arial", 18)).grid(row=0, column=0, padx=(8, 8), pady=6, sticky="nw")

        self.footer_status_lbl = ctk.CTkLabel(
            footer_frame, text="No ride selected", text_color="white", anchor="w", font=("Arial", 12, "bold"))
        self.footer_status_lbl.grid(
            row=0, column=1, sticky="nw", padx=(0, 6), pady=(8, 1))

        self.footer_pickup_lbl = ctk.CTkLabel(
            footer_frame, text="Pickup: -", text_color="white", anchor="w", font=("Arial", 10))
        self.footer_pickup_lbl.grid(row=1, column=1, sticky="w", padx=(0, 6))

        self.footer_drop_lbl = ctk.CTkLabel(
            footer_frame, text="Drop: -", text_color="white", anchor="w", font=("Arial", 10))
        self.footer_drop_lbl.grid(
            row=2, column=1, sticky="w", padx=(0, 6), pady=(0, 6))
        self.footer_date_lbl = ctk.CTkLabel(
            footer_frame, text="Date: -", text_color="white", anchor="w", font=("Arial", 10))
        self.footer_date_lbl.grid(row=3, column=1, sticky="w", padx=(0, 6))
        self.footer_time_lbl = ctk.CTkLabel(
            footer_frame, text="Time: -", text_color="white", anchor="w", font=("Arial", 10))
        self.footer_time_lbl.grid(
            row=4, column=1, sticky="w", padx=(0, 6), pady=(0, 6))
        self.footer_rating_lbl = ctk.CTkLabel(
            footer_frame, text="Rating: -", text_color="white", anchor="w", font=("Arial", 10, "bold"))
        self.footer_rating_lbl.grid(
            row=5, column=1, sticky="w", padx=(0, 6), pady=(0, 6))

        self._select_card(self.selected_card)  

        #  RATING UI SETUP
        self._setup_rating_ui()
        self.rating_card.grid_remove()

        try:
            self._refresh_ride_status()
        except Exception as e:
            print(f"Error checking active ride on startup: {e}")
            self.ride_info = None

    def _refresh_ride_status(self):

        if getattr(self, "rating_card", None) and self.rating_card.winfo_ismapped():
            self.after(5000, self._refresh_ride_status)
            return

        try:
            latest_ride = get_active_ride(self.user_id)
            if latest_ride:
                def s_addr(f_addr): return ", ".join(
                    [p.strip() for p in f_addr.split(",") if p.strip()][:2])
                if len(latest_ride) >= 9:
                    pu, de = latest_ride[1], latest_ride[2]
                    sd, st = latest_ride[7], latest_ride[8]
                    latest_ride = (latest_ride[0], s_addr(pu), s_addr(
                        de), latest_ride[3], latest_ride[4], latest_ride[5], latest_ride[6], sd, st)
                self.ride_info = latest_ride
                self.show_active_ride()
        except Exception as e:
            print(f"Error refreshing ride status: {e}")
            self.after(5000, self._refresh_ride_status)

    def _select_card(self, name, event=None):
        self.selected_card = name
        dark_highlight, dark_surface = "#1c3d52", "#343638"
        if name == "normal":
            self.card_normal.configure(
                fg_color=dark_highlight, border_width=2, border_color="#06b6a4")
            self.card_comfort.configure(fg_color=dark_surface, border_width=0)
        else:
            self.card_normal.configure(fg_color=dark_surface, border_width=0)
            self.card_comfort.configure(
                fg_color=dark_highlight, border_width=2, border_color="#06b6a4")
        self._compute_distance_and_fare()

    def _update_location(self, type_str, latlng, address_str=None):
        lat, lon = latlng

        if type_str == "from":
            if self.from_marker:
                self.from_marker.delete()
            self.from_loc = (lat, lon)
            self.from_marker = self.map_widget.set_marker(
                lat, lon, text="From")
        else:
            if self.to_marker:
                self.to_marker.delete()
            self.to_loc = (lat, lon)
            self.to_marker = self.map_widget.set_marker(lat, lon, text="To")

        input_widget = self.input_from if type_str == "from" else self.input_to
        input_widget.delete(0, tk.END)

        text = address_str or f"{lat:.5f}, {lon:.5f}"
        input_widget.insert(0, text)

        self._compute_distance_and_fare()
        self._draw_route()

    def _draw_route(self):
        if self.current_path:
            self.current_path.delete()
            self.current_path = None
        if not (self.from_loc and self.to_loc):
            return

        coords = self.get_route_osrm(self.from_loc, self.to_loc)
        try:
            self.current_path = self.map_widget.set_path(
                coords, width=4) if coords else self.map_widget.set_path([self.from_loc, self.to_loc], width=3)
        except Exception:
            self.current_path = self.map_widget.set_path(
                coords) if coords else self.map_widget.set_path([self.from_loc, self.to_loc])

    def get_route_osrm(self, from_loc, to_loc):
        try:
            url = f"https://router.project-osrm.org/route/v1/driving/{from_loc[1]},{from_loc[0]};{to_loc[1]},{to_loc[0]}?overview=full&geometries=geojson"
            resp = requests.get(url, timeout=8)
            if resp.status_code != 200:
                return None
            data = resp.json()
            if not data.get("routes"):
                return None
            geom = data["routes"][0]["geometry"]["coordinates"]
            return [(pt[1], pt[0]) for pt in geom]
        except Exception as e:
            print("OSRM error:", e)
            return None

    def _setup_rating_ui(self):
        """Builds the dedicated rating interface which overlays the main screen."""
        self.rating_card = ctk.CTkFrame(
            self, fg_color="#1f1f1f", corner_radius=10)
        self.rating_card.grid_columnconfigure(0, weight=1)
        self.rating_card.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)

        ctk.CTkLabel(self.rating_card, text="Ride Completed!", font=ctk.CTkFont(
            size=24, weight="bold")).grid(row=0, column=0, pady=(40, 5), padx=20)
        ctk.CTkLabel(self.rating_card, text="Please rate your driver to complete the ride process.",
                     font=ctk.CTkFont(size=14), text_color="white").grid(row=1, column=0, pady=(0, 20), padx=20)

        # Rating Selector Frame
        rating_frame = ctk.CTkFrame(self.rating_card, fg_color="transparent")
        rating_frame.grid(row=2, column=0, pady=20)
        rating_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        self.star_buttons = []
        for i in range(1, 6):
            btn = ctk.CTkButton(
                rating_frame,
                text="★",
                command=lambda r=i: self._select_rating(r),
                width=50, height=50,
                fg_color="#343638",
                hover_color="#5E6061",
                text_color="#F8C300"
            )
            btn.grid(row=0, column=i-1, padx=5)
            self.star_buttons.append(btn)

        self.lbl_rating_text = ctk.CTkLabel(
            self.rating_card, text="Select a rating (1-5)", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_rating_text.grid(row=3, column=0, pady=(20, 10))

        # Submit Button
        ctk.CTkButton(
            self.rating_card,
            text="Submit Rating",
            command=self._submit_rating,
            fg_color="#00C48C", hover_color="#009f74",
            width=200, height=40
        ).grid(row=4, column=0, pady=(20, 40))

    def _select_rating(self, rating):
        """Handles visual selection of the star rating."""
        self.rating_value = rating
        self.lbl_rating_text.configure(
            text=f"Selected: {rating} Star{'s' if rating > 1 else ''}!")
        for i, btn in enumerate(self.star_buttons):
            if i < rating:
                btn.configure(fg_color="#F8C300", text_color="black")
            else:
                btn.configure(fg_color="#343638", text_color="#F8C300")

    def _handle_rating_required(self, ride_data):
        """ [MIXIN HOOK] Show rating UI when a ride is completed and needs rating.
            Ensures tuple unpacking handles 9 elements."""

        ride_data = tuple(ride_data) + (None,) * (9 - len(ride_data))
        ride_id, pickup, dest, status, fare, self.current_driver_id, rating, sched_date, sched_time = ride_data
        self.current_ride_id = ride_id

        if getattr(self, "rating_card", None) and self.rating_card.winfo_ismapped():
            return

    #  Hide dashboard UI
        self.map_card.grid_remove()
        self.right_panel.grid_remove()
        self.update_idletasks()

    #  Show Rating UI
        self.rating_card.grid(row=0, column=0, columnspan=2,
                              padx=14, pady=14, sticky="nsew")
        self.rating_card.lift()
        self.update_idletasks()

    #  Reset rating visuals
        self.rating_value = 0
        for btn in self.star_buttons:
            btn.configure(fg_color="#343638", text_color="#F8C300") 
        self.lbl_rating_text.configure(text="Select a rating (1-5)")

    def _submit_rating(self):
        """Submit the selected rating and restore the dashboard UI."""
        if self.rating_value == 0:
            messagebox.showwarning(
                "Warning", "Please select a star rating before submitting.")
            return

        ride_id = self.current_ride_id

        success = submit_driver_rating(ride_id, self.rating_value)

        if success:
            messagebox.showinfo("Success", "Thank you for rating your driver!")

            self.rating_card.grid_remove()
            self.map_card.grid(row=0, column=0, padx=(
                14, 7), pady=14, sticky="nsew")
            self.right_panel.grid(row=0, column=1, padx=(
                7, 14), pady=14, sticky="nsew")
            self.update_idletasks()

            try:
                updated_ride = get_active_ride(self.user_id, ride_id=ride_id)
                if updated_ride:
                    self.ride_info = updated_ride
                    self.current_ride_id = updated_ride[0]
                    self.show_active_ride()  # UI reflects new rating immediately
            except Exception as e:
                print("Error refreshing ride after rating:", e)
        else:
            messagebox.showerror(
                "Error", "Could not submit rating. Check console for details.")

    def update_time(self):
        """Updates date & time every second."""
        try:
            now = datetime.now().strftime("📅 %Y-%m-%d   ⏰ %I:%M %p")
            if getattr(self, "datetime_label", None):
                self.datetime_label.configure(text=now)
        except Exception:
            pass

        try:
            self.after(1000, self.update_time)
        except Exception:
            pass


if __name__ == "__main__":
    app = PassengerDashboard(1)
    app.mainloop()
