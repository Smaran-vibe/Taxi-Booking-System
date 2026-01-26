# passenger_constants.py

import math
import subprocess


KATHMANDU_CENTER = (27.7172, 85.3240)
INITIAL_ZOOM = 12

# Nepal boundaries
NEPAL_MIN_LAT = 26.347
NEPAL_MAX_LAT = 30.447
NEPAL_MIN_LON = 80.058
NEPAL_MAX_LON = 88.201

# Pricing
PRICE_NORMAL = 30.0
PRICE_COMFORT = 45.0
RATES = {"normal": PRICE_NORMAL, "comfort": PRICE_COMFORT}

# Utility Functions 

def logout(window=None):
    """
    Safe logout helper: destroy provided window (if any) and reopen login window.
    This uses a subprocess to launch the Login script.
    """
    if window:
        try:
            window.destroy()  
        except Exception:
            pass

    subprocess.Popen(["python", "main.py"])

def is_inside_nepal(lat, lon):
    """Checks if a coordinate pair is within the defined Nepal bounding box."""
    return (NEPAL_MIN_LAT <= lat <= NEPAL_MAX_LAT) and \
           (NEPAL_MIN_LON <= lon <= NEPAL_MAX_LON)

def haversine_km(lat1, lon1, lat2, lon2):
    """Calculates the great-circle distance between two points on the Earth."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c