# booking_management.py
import threading
from tkinter import messagebox
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from datetime import datetime, date
from passenger_constants import haversine_km

from database import create_ride, get_active_ride, cancel_ride


class BookingManagementMixin:


    def __init__(self):
        self.ride_info = None
        self.ride_active = False
        self.ride_status = "No ride"
        self.current_ride_id = None

        if not hasattr(self, "geolocator") or self.geolocator is None:
            try:
                from geopy.geocoders import Nominatim
                self.geolocator = Nominatim(user_agent="taxi_booking_app_v1")
            except Exception:
                self.geolocator = None

    #  BOOK RIDE
    def _confirm_ride(self):
        """Called when passenger clicks Book Ride.
        Converts coords -> addresses (if coords present), then inserts ride to DB.
        """

        if not (getattr(self, "from_loc", None) and getattr(self, "to_loc", None)):
            messagebox.showinfo("Select locations",
                                "Please select both From and To locations.")
            return

        # reverse geocode
        pickup_name = None
        dest_name = None
        try:
            if self.geolocator:
                try:
                    flt, flon = self.from_loc
                    loc_from = self.geolocator.reverse(
                        f"{flt}, {flon}", timeout=10)
                    pickup_name = loc_from.address if loc_from and getattr(
                        loc_from, "address", None) else None
                except (GeocoderTimedOut, GeocoderServiceError, Exception):
                    pickup_name = None

                try:
                    tlt, tlon = self.to_loc
                    loc_to = self.geolocator.reverse(
                        f"{tlt}, {tlon}", timeout=10)
                    dest_name = loc_to.address if loc_to and getattr(
                        loc_to, "address", None) else None
                except (GeocoderTimedOut, GeocoderServiceError, Exception):
                    dest_name = None

            if not pickup_name:
                pickup_name = f"{self.from_loc[0]:.5f}, {self.from_loc[1]:.5f}"
            if not dest_name:
                dest_name = f"{self.to_loc[0]:.5f}, {self.to_loc[1]:.5f}"
        except Exception as e:
            print("Reverse geocoding error:", e)
            pickup_name = f"{self.from_loc[0]:.5f}, {self.from_loc[1]:.5f}"
            dest_name = f"{self.to_loc[0]:.5f}, {self.to_loc[1]:.5f}"

        # distance & fare
        try:

            d = haversine_km(
                self.from_loc[0], self.from_loc[1], self.to_loc[0], self.to_loc[1])
        except Exception:
            d = getattr(self, "last_distance_km", 0.0)

        try:
            rate = self.rates[self.selected_card]
        except Exception:
            rate = 30.0
        fare = d * rate
        self.last_distance_km = d
        self.last_fare = fare

        confirm = messagebox.askyesno(
            "Confirm Ride",
            f"From: {pickup_name}\n"
            f"To: {dest_name}\n"
            f"Distance: {d:.2f} km\n"
            f"Fare: Rs {fare:.2f}\n\n"
            "Confirm booking?"
        )
        if not confirm:
            return
       # schedule date/time
        try:
            # DATE VALIDATION
            if hasattr(self, "entry_date") and self.entry_date.get().strip():
                ds = self.entry_date.get().strip()
                try:
                    dobj = datetime.strptime(ds, "%Y-%m-%d").date()
                    if dobj < date.today():
                        messagebox.showerror(
                            "Invalid Date", "Please enter a appropriate time.")
                        return
                    sched_date = ds
                except ValueError:
                    messagebox.showerror(
                        "Invalid Format", "Please enter date as YYYY-MM-DD.")
                    return
            else:
                messagebox.showerror("Required", "Please enter a pickup date.")
                return

            if hasattr(self, "entry_time") and self.entry_time.get().strip():
                ts = self.entry_time.get().strip()
                try:
                    datetime.strptime(ts, "%H:%M")
                    sched_time = ts
                except ValueError:
                    messagebox.showerror(
                        "Invalid Format", "Please enter time as HH:MM (24h).")
                    return
            else:
                messagebox.showerror("Required", "Please enter a pickup time.")
                return

            ride_id = create_ride(
                self.user_id, pickup_name, dest_name, fare, "Requested",
                scheduled_date=sched_date, scheduled_time=sched_time
            )
        except Exception as e:
            messagebox.showerror(
                "Database Error", f"Could not create ride: {e}")
            return

        self.current_ride_id = ride_id
        try:
            self.ride_info = get_active_ride(self.user_id)
        except Exception:
            self.ride_info = None

        self.ride_active = True
        self.ride_status = "Requested"

        # Update passenger UI widgets
        try:
            self.lbl_status_value.configure(text="Requested ⏳")
            self.btn_cancel_ride.grid()
            def short(s): return ", ".join([p.strip()
                                            for p in str(s).split(",")][:2])
            self.footer_status_lbl.configure(text="Ride Requested")
            self.footer_pickup_lbl.configure(
                text=f"Pickup: {short(pickup_name)}")
            self.footer_drop_lbl.configure(text=f"Drop: {short(dest_name)}")
            try:
                self.footer_date_lbl.configure(
                    text=f"Date: {sched_date if sched_date else '-'}")
                self.footer_time_lbl.configure(
                    text=f"Time: {sched_time if sched_time else '-'}")
            except Exception:
                pass
        except Exception:
            pass

        messagebox.showinfo("Booked", "Ride request sent to drivers.")

    #  CANCEL RIDE
    def _cancel_ride(self):
        """Cancel active ride. Updates DB via cancel_ride(ride_id, new_status)."""
        if not getattr(self, "ride_active", False) and not getattr(self, "ride_info", None):
            messagebox.showinfo("Cancel", "No active ride to cancel.")
            return

        ok = messagebox.askyesno(
            "Cancel Ride", "Are you sure you want to cancel this ride?")
        if not ok:
            return

        ride_id = getattr(self, "current_ride_id", None) or (
            self.ride_info[0] if self.ride_info else None)
        if not ride_id:
            messagebox.showwarning(
                "Cancel", "Unable to determine ride id to cancel.")
            return

        try:
            cancel_ride(ride_id, new_status="Cancelled")
        except Exception as e:
            print("Error cancelling ride:", e)

        # update local state + UI
        self.ride_active = False
        self.ride_status = "Cancelled"
        self.current_ride_id = None
        self.ride_info = None
        try:
            self.lbl_status_value.configure(text="Cancelled ❌")
            self.btn_cancel_ride.grid_remove()
            self.footer_status_lbl.configure(text="Ride Cancelled")
        except Exception:
            pass

        try:
            self._reset_ride_selection()
        except Exception:
            pass

        messagebox.showinfo("Ride Cancelled", "Your ride has been cancelled.")

    #  SHOW / LOAD ACTIVE RIDE
    def show_active_ride(self):

        try:
            if self.ride_info:
                active = self.ride_info
            elif self.current_ride_id:
                active = get_active_ride(
                    self.user_id, ride_id=self.current_ride_id)
            else:
                active = get_active_ride(self.user_id)
        except Exception as e:
            print("Error fetching active ride:", e)
            active = None

        if not active:

            self.ride_info = None
            self.ride_active = False
            self.current_ride_id = None
            try:
                self.lbl_status_value.configure(text="No ride booked")
                self.btn_cancel_ride.grid_remove()
                self.footer_status_lbl.configure(text="No active ride")
                self.footer_pickup_lbl.configure(text="Pickup: -")
                self.footer_drop_lbl.configure(text="Drop: -")
            except Exception:
                pass
            return

        # Normalize tuple length
        active = tuple(active) + (None,) * (9 - len(active))
        ride_id, pickup, destination, status, fare, driver_id, rating, scheduled_date, scheduled_time = active
        print(
            f"DEBUG: show_active_ride - Fetched rating: {rating}, Status: {status}")

        # set mixin state
        self.ride_info = active
        self.current_ride_id = ride_id
        self.ride_active = True
        self.ride_status = str(status) if status is not None else "Requested"

       
        try:
            status_clean = str(status).capitalize() if status else "Requested"
            self.lbl_status_value.configure(text=status_clean)
            self.footer_status_lbl.configure(text=f"Ride {status_clean}")

            def short(s): return ", ".join(
                [p.strip() for p in str(s).split(",")][:2]) if s else "-"
            self.footer_pickup_lbl.configure(text=f"Pickup: {short(pickup)}")
            self.footer_drop_lbl.configure(text=f"Drop: {short(destination)}")
            if scheduled_date:
                self.footer_date_lbl.configure(text=f"Date: {scheduled_date}")
            else:
                self.footer_date_lbl.configure(text="Date: -")
            if scheduled_time:
                self.footer_time_lbl.configure(text=f"Time: {scheduled_time}")
            else:
                self.footer_time_lbl.configure(text="Time: -")
            if rating is not None:
                self.footer_rating_lbl.configure(
                    text=f"Rating: {rating:.2f}/5 ★")
            else:
                self.footer_rating_lbl.configure(text="Rating: N/A")
        except Exception:
            pass

        # show/cancel button
        try:
            if str(status).lower() in ("requested", "pending", "accepted"):
                self.btn_cancel_ride.grid()
            else:
                self.btn_cancel_ride.grid_remove()
        except Exception:
            pass

        # store current driver id
        try:
            self.current_driver_id = int(driver_id) if driver_id else None
        except Exception:
            self.current_driver_id = None

        
        try:
            if str(status).lower() == "completed" and (rating is None):

                if hasattr(self, "_handle_rating_required"):
                    print(
                        f"DEBUG: Calling _handle_rating_required with: {active}")
                    self._handle_rating_required(active)
        except Exception:
            pass

   
        return
