# geo_routing.py

import tkinter as tk
from tkinter import messagebox
import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from passenger_constants import is_inside_nepal, haversine_km, PRICE_NORMAL, PRICE_COMFORT
import time


class GeoRoutingMixin:
    """Methods for location searching, map drawing, and OSRM routing."""

    def __init__(self):
        self.geolocator = Nominatim(user_agent="taxi_booking_app_v1")

        if not hasattr(self, "rates"):
            self.rates = {
                "normal": PRICE_NORMAL,
                "comfort": PRICE_COMFORT
            }
        if not hasattr(self, "selected_card"):
            self.selected_card = "normal"

    def _set_selecting_mode(self, mode):
        highlight_color = "#e6f2ff"
        default_color = "white"

        if getattr(self, "input_from", None):
            self.input_from.configure(
                fg_color=highlight_color if mode == "from" else default_color)

        if getattr(self, "input_to", None):
            self.input_to.configure(
                fg_color=highlight_color if mode == "to" else default_color)

        self.selecting_mode = mode

    def _set_from_on_map_click(self, coords):
        if is_inside_nepal(coords[0], coords[1]):
            self._update_location("from", coords)
            self._compute_distance_and_fare()
        else:
            messagebox.showwarning("Out of Service Area",
                                   "Sorry, we currently only operate within Nepal.")

    def _set_to_on_map_click(self, coords):
        if is_inside_nepal(coords[0], coords[1]):
            self._update_location("to", coords)
            self._compute_distance_and_fare()
        else:
            messagebox.showwarning("Out of Service Area",
                                   "Sorry, destination must be within Nepal.")

    def _geocode_and_update_map(self, type_str, query):
        try:
            location = self.geolocator.geocode(
                query, country_codes="np", language="en", timeout=10)

            if not location:
                location = self.geolocator.geocode(
                    f"{query}, Nepal", language="en", timeout=10)

            if location:
                if is_inside_nepal(location.latitude, location.longitude):

                    self._update_location(
                        type_str,
                        (location.latitude, location.longitude),
                        location.address
                    )

                    if getattr(self, "map_widget", None):
                        try:
                            self.map_widget.set_position(
                                location.latitude, location.longitude)
                            self.map_widget.set_zoom(14)
                        except:
                            pass

                    self._compute_distance_and_fare()

                else:
                    messagebox.showwarning("Location Restriction",
                                           f"'{query}' was found but is outside Nepal.")
            else:
                messagebox.showerror("Location Not Found",
                                     f"Could not find '{query}'. Try a place in Nepal.")

        except (GeocoderTimedOut, GeocoderServiceError) as e:
            messagebox.showerror("Connection Error",
                                 f"Network error: {e}. Check your internet.")
        except Exception as ex:
            print("Unexpected error in geocode:", ex)

    def _search_location_from(self, event=None):
        q = self.input_from.get().strip()
        if q:
            self._geocode_and_update_map("from", q)

    def _search_location_to(self, event=None):
        q = self.input_to.get().strip()
        if q:
            self._geocode_and_update_map("to", q)

    def _get_route_osrm(self, start, end, retries=1):
        try:
            s_lat, s_lon = float(start[0]), float(start[1])
            e_lat, e_lon = float(end[0]), float(end[1])

            url = (
                "https://router.project-osrm.org/route/v1/driving/"
                f"{s_lon:.6f},{s_lat:.6f};{e_lon:.6f},{e_lat:.6f}"
                "?overview=full&geometries=geojson&alternatives=false&steps=true"
            )
            print(f"OSRM Request URL: {url}")

            for attempt in range(retries + 1):
                try:
                    resp = requests.get(url, timeout=10)
                    print(f"OSRM Response Status: {resp.status_code}")
                    
                    print(f"OSRM Response Content: {resp.text[:500]}...")
                    resp.raise_for_status() 
                except requests.exceptions.RequestException as req_err:
                    print(
                        f"OSRM Request Error (Attempt {attempt+1}/{retries+1}): {req_err}")
                    if attempt < retries:
                        time.sleep(0.5)
                        continue
                    return None
                except Exception as e:
                    print(
                        f"OSRM Unexpected Error (Attempt {attempt+1}/{retries+1}): {e}")
                    if attempt < retries:
                        time.sleep(0.5)
                        continue
                    return None

                try:
                    data = resp.json()
                except ValueError as json_err:
                    print(f"OSRM JSON Decoding Error: {json_err}")
                    return None

                if "routes" not in data or not data["routes"]:
                    print("OSRM Error: No routes found in response.")
                    return None

                route_geometry = data["routes"][0]["geometry"]
                if route_geometry.get("type") != "LineString" or "coordinates" not in route_geometry:
                    print(
                        f"OSRM Error: Expected GeoJSON LineString, but got type {route_geometry.get("type")} or missing coordinates.")
                    return None

                geometry = route_geometry["coordinates"]

                return [(float(pt[1]), float(pt[0])) for pt in geometry]

            return None

        except Exception as e:
            print("OSRM General Error:", e)
            return None

    def _draw_route(self):
        if getattr(self, "current_path", None):
            try:
                self.current_path.delete()
            except:
                pass
            self.current_path = None

        if not (self.from_loc and self.to_loc):
            return

        try:
            self.from_loc = (float(self.from_loc[0]), float(self.from_loc[1]))
            self.to_loc = (float(self.to_loc[0]), float(self.to_loc[1]))
        except:
            pass

        route_points = self._get_route_osrm(self.from_loc, self.to_loc)

        if route_points:
            try:
                self.current_path = self.map_widget.set_path(
                    route_points, color="blue", width=4)
            except Exception as e:
                print(f"Error drawing OSRM route: {e}")
                messagebox.showwarning(
                    "Routing Error", "Could not draw detailed route. Drawing straight line instead.")
                self.current_path = self.map_widget.set_path(
                    [self.from_loc, self.to_loc], color="blue", width=3)
        else:
            messagebox.showwarning(
                "Routing Error", "Could not get detailed route from OSRM. Drawing straight line instead.")
            try:
                self.current_path = self.map_widget.set_path(
                    [self.from_loc, self.to_loc], color="blue", width=3)
            except Exception as e:
                print(f"Error drawing straight line route: {e}")

        self._compute_distance_and_fare()

    def normalize_coord(self, coord):
        """
         Fix coordinates loaded from DB in wrong order or as strings.
         Ensures final output is (lat, lon)
        """
    # Convert string 
        if isinstance(coord, str):
            parts = coord.replace("(", "").replace(")", "").split(",")
            coord = (float(parts[0]), float(parts[1]))

        lat, lon = float(coord[0]), float(coord[1])

    
        if lat > 90:
            lat, lon = lon, lat

        return (lat, lon)

    def _compute_distance_and_fare(self):
        """Distance & Fare updater method INSIDE the class."""
        if not (self.from_loc and self.to_loc):
            return

        try:
            lat1, lon1 = map(float, self.from_loc)
            lat2, lon2 = map(float, self.to_loc)

            distance_km = haversine_km(lat1, lon1, lat2, lon2)

            distance_text = f"Distance: {distance_km:.2f} km"
            hint_text = f"Distance\n{distance_km:.2f} km"

            if getattr(self, "lbl_distance", None):
                self.lbl_distance.configure(text=distance_text)

            if getattr(self, "lbl_distance_hint", None):
                self.lbl_distance_hint.configure(text=hint_text)

            rate = self.rates.get(self.selected_card, PRICE_NORMAL)
            fare = distance_km * rate

            fare_text = f"Fare: Rs {fare:.2f}"

            if getattr(self, "lbl_fare", None):
                self.lbl_fare.configure(text=fare_text)

        except Exception as e:
            print("Distance/Fare error:", e)
