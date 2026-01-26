import database as db
import sqlite3

DB_NAME = db.DB_NAME


def get_total_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM passenger")
    p = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM driver")
    d = cursor.fetchone()[0]

    total = p + d
    conn.close()
    return total


def get_total_bookings():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM rides")
    total = cursor.fetchone()[0]

    conn.close()
    return total


def get_total_payments():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(fare) FROM rides WHERE status='Completed'")
    total = cursor.fetchone()[0]

    conn.close()
    return total if total else 0


def admin_get_all_bookings():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT r.id, 
               p.name AS passenger_name,
               r.pickup,
               r.destination,
               r.status,
               r.fare,
               r.scheduled_date, -- Ensure scheduled_date is included
               r.scheduled_time
        FROM rides r
        JOIN passenger p ON r.passenger_id = p.id
        ORDER BY r.id DESC
    """)
    rows = cursor.fetchall()

    conn.close()
    return rows


def admin_get_all_drivers_with_ratings():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            d.id, 
            d.name, 
            d.phone, 
            AVG(dr.rating) AS average_rating
        FROM driver d
        LEFT JOIN driver_ratings dr ON d.id = dr.driver_id
        GROUP BY d.id, d.name, d.phone
        ORDER BY d.name
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


def admin_get_scheduled_bookings():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT r.id, 
               p.name AS passenger_name,
               r.pickup,
               r.destination,
               r.status,
               r.fare,
               r.scheduled_date,
               r.scheduled_time
        FROM rides r
        JOIN passenger p ON r.passenger_id = p.id
        WHERE r.scheduled_date IS NOT NULL OR r.scheduled_time IS NOT NULL
        ORDER BY r.scheduled_date DESC, r.scheduled_time DESC
    """)
    rows = cursor.fetchall()

    conn.close()
    return rows


def admin_get_all_users():
    """Fetch all passengers and drivers from the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, email
        FROM passenger
    """)
    passengers = cursor.fetchall()

    cursor.execute("""
        SELECT id, name, email
        FROM driver
    """)
    drivers = cursor.fetchall()

    conn.close()

    users = []

    for p in passengers:
        users.append((p[0], p[1], p[2], "Null"))

    for d in drivers:
        users.append((d[0], d[1], d[2], "Null"))

    return users


def admin_get_all_payments():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            r.id,
            p.name AS passenger_name,
            r.fare,
            r.status
        FROM rides r
        JOIN passenger p ON r.passenger_id = p.id
        WHERE r.status = 'Completed'
        ORDER BY r.id DESC
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows
