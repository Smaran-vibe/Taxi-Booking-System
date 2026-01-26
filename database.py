import sqlite3
import bcrypt

DB_NAME = "taxi_booking.db"


def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS driver (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        password TEXT NOT NULL,
        license_number TEXT UNIQUE NOT NULL,
        is_busy INTEGER DEFAULT 0,
        current_ride_id INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS passenger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rides (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        passenger_id INTEGER NOT NULL,
        driver_id INTEGER,
        pickup TEXT NOT NULL,
        destination TEXT NOT NULL,
        status TEXT DEFAULT 'Requested',
        fare REAL,

         NEW FIELDS FOR SCHEDULED BOOKING
        scheduled_date TEXT,          
        scheduled_time TEXT,          
        scheduled_datetime TEXT,      

         FOR ADMIN ASSIGN DRIVER
        assigned_by_admin INTEGER DEFAULT 0,
        assigned_at TEXT,

        cancel_requested INTEGER DEFAULT 0,
        rating INTEGER DEFAULT NULL
    );
    """
    )

    # Add new columns to rides table 
    cursor.execute("PRAGMA table_info(rides)")
    columns = [column[1] for column in cursor.fetchall()]

    if 'scheduled_date' not in columns:
        cursor.execute("ALTER TABLE rides ADD COLUMN scheduled_date TEXT")
    if 'scheduled_time' not in columns:
        cursor.execute("ALTER TABLE rides ADD COLUMN scheduled_time TEXT")
    if 'scheduled_datetime' not in columns:
        cursor.execute("ALTER TABLE rides ADD COLUMN scheduled_datetime TEXT")
    if 'assigned_by_admin' not in columns:
        cursor.execute("ALTER TABLE rides ADD COLUMN assigned_by_admin INTEGER DEFAULT 0")

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS driver_ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ride_id INTEGER,
        driver_id INTEGER,
        rating INTEGER,
        comment TEXT,
        FOREIGN KEY (ride_id) REFERENCES rides(id),
        FOREIGN KEY (driver_id) REFERENCES driver(id)
    )
    """)

   
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS driver_notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_id INTEGER NOT NULL,
        ride_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (driver_id) REFERENCES driver(id),
        FOREIGN KEY (ride_id) REFERENCES rides(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS passenger_notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        passenger_id INTEGER NOT NULL,
        ride_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (passenger_id) REFERENCES passenger(id),
        FOREIGN KEY (ride_id) REFERENCES rides(id)
    )
    """)

    conn.commit()
    conn.close()
    print("Tables created successfully!")


def is_email_registered_elsewhere(email, current_role):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    tables = {
        "admin": "admin",
        "driver": "driver",
        "passenger": "passenger"
    }

    for role, table in tables.items():
        if role == current_role:
            continue

        if role == "admin":
            cursor.execute("SELECT * FROM admin WHERE username=?", (email,))
        else:
            cursor.execute(f"SELECT * FROM {table} WHERE email=?", (email,))

        if cursor.fetchone():
            conn.close()
            return role

    conn.close()
    return None


#  REGISTER FUNCTIONS 

def register_admin(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM admin")
    count = cursor.fetchone()[0]

    if count > 0:
        conn.close()
        return "exists"

    try:
        hashed_password = bcrypt.hashpw(password.strip().encode('utf-8'), bcrypt.gensalt())
        cursor.execute(
            "INSERT INTO admin (id, username, password) VALUES (1, ?, ?)",
            (username.strip(), hashed_password.decode('utf-8'))
        )
        conn.commit()
        return True
    
    except Exception as e:
        print("Admin Registration Error:",e)
        return False
    
    finally:
        conn.close()


def login_admin(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM admin WHERE username=? AND password=?",
        (username.strip(), password.strip())
    )

    result = cursor.fetchone()
    conn.close()
    return result


def register_driver(name, email, password, license_number):
    conflict = is_email_registered_elsewhere(email, "driver")
    if conflict:
        return f"email-exists-in-{conflict}"

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    debug_message = f"DEBUG: register_passenger - Registering email: {email}, password: {password.strip()}"
    with open("debug_log.txt", "a") as f:
        f.write(debug_message + "\n")
    try:
        hashed_password = bcrypt.hashpw(password.strip().encode('utf-8'), bcrypt.gensalt())
        cursor.execute("""
            INSERT INTO driver (name, email, password, license_number)
            VALUES (?, ?, ?, ?)
        """, (name, email, hashed_password.decode('utf-8'), license_number))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def register_passenger(name, email, password):
    conflict = is_email_registered_elsewhere(email, "passenger")
    if conflict:
        return f"email-exists-in-{conflict}"

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        hashed_password = bcrypt.hashpw(password.strip().encode('utf-8'), bcrypt.gensalt())
        cursor.execute("""
            INSERT INTO passenger (name, email, password)
            VALUES (?, ?, ?)
        """, (name, email.strip(), hashed_password.decode('utf-8')))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()



def login_user(username_or_email, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    debug_message_admin = f"DEBUG: login_user - Checking Admin with email: {username_or_email.strip()}"
    with open("debug_log.txt", "a") as f:
        f.write(debug_message_admin + "\n")
    cursor.execute(
        "SELECT id, username, password FROM admin WHERE username=?",
        (username_or_email.strip(),)
    )
    admin = cursor.fetchone()
    if admin and bcrypt.checkpw(password.strip().encode('utf-8'), admin[2].encode('utf-8')):
        conn.close()
        return ("Admin", admin)

    debug_message_driver = f"DEBUG: login_user - Checking Driver with email: {username_or_email.strip()}"
    with open("debug_log.txt", "a") as f:
        f.write(debug_message_driver + "\n")
    cursor.execute(
        "SELECT id, name, email, phone, password FROM driver WHERE email=?",
        (username_or_email.strip(),)
    )
    driver = cursor.fetchone()
    if driver and bcrypt.checkpw(password.strip().encode('utf-8'), driver[4].encode('utf-8')):
        return ("Driver", driver)

    debug_message_passenger = f"DEBUG: login_user - Checking Passenger with email: {username_or_email.strip()}"
    with open("debug_log.txt", "a") as f:
        f.write(debug_message_passenger + "\n")
    cursor.execute(
        "SELECT id, name, email, password FROM passenger WHERE email=?",
        (username_or_email.strip(),)
    )
    passenger = cursor.fetchone()
    if passenger and bcrypt.checkpw(password.strip().encode('utf-8'), passenger[3].encode('utf-8')):
        conn.close()
        return ("Passenger", passenger)

    conn.close()
    return None



def create_ride(passenger_id, pickup, destination, fare, status,
                scheduled_date=None, scheduled_time=None):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Combine into one datetime 
    scheduled_datetime = None
    if scheduled_date and scheduled_time:
        scheduled_datetime = f"{scheduled_date} {scheduled_time}"

    cursor.execute("""
        INSERT INTO rides (
            passenger_id, pickup, destination, fare, status,
            scheduled_date, scheduled_time, scheduled_datetime
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (passenger_id, pickup, destination, fare, status,
          scheduled_date, scheduled_time, scheduled_datetime))

    conn.commit()
    ride_id = cursor.lastrowid
    conn.close()
    return ride_id



def get_active_ride(user_id, ride_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    print(f"DEBUG: get_active_ride called with user_id={user_id}, ride_id={ride_id}")

    if ride_id:
        cursor.execute("""
            SELECT id, pickup, destination, status, fare, driver_id, rating,
                   scheduled_date, scheduled_time
            FROM rides
            WHERE id=? AND passenger_id=? AND status IN ('Requested','Accepted','Completed')
        """, (ride_id, user_id))
    else:
        cursor.execute("""
            SELECT id, pickup, destination, status, fare, driver_id, rating,
                   scheduled_date, scheduled_time
            FROM rides
            WHERE passenger_id=? AND status IN ('Requested','Accepted','Completed')
            ORDER BY id DESC
            LIMIT 1
        """, (user_id,))
    ride = cursor.fetchone()
    conn.close()
    return ride




def cancel_ride(ride_id, new_status="Cancelled"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT driver_id FROM rides WHERE id=?", (ride_id,))
    d = cursor.fetchone()

    cursor.execute("UPDATE rides SET status=? WHERE id=?", (new_status, ride_id))

    if d and d[0]:
        cursor.execute("""
            UPDATE driver
            SET is_busy=0, current_ride_id=NULL
            WHERE id=?
        """, (d[0],))

    conn.commit()
    conn.close()



def submit_driver_rating(ride_id, rating_value):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE rides
            SET rating=?
            WHERE id=?
        """, (rating_value, ride_id))

        cursor.execute("SELECT driver_id FROM rides WHERE id=?", (ride_id,))
        row = cursor.fetchone()
        driver_id = row[0] if row else None

        if driver_id:
            cursor.execute("SELECT id FROM driver_ratings WHERE ride_id=?", (ride_id,))
            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    "UPDATE driver_ratings SET rating=? WHERE id=?",
                    (rating_value, existing[0])
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO driver_ratings (ride_id, driver_id, rating, comment)
                    VALUES (?, ?, ?, ?)
                    """,
                    (ride_id, driver_id, rating_value, "")
                )

        conn.commit()
        return True
    except Exception as e:
        print("Rating Error:", e)
        return False
    finally:
        conn.close()


def driver_accept_ride(driver_id, ride_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM rides 
        WHERE driver_id=? AND status='Accepted'
    """, (driver_id,))
    active = cursor.fetchone()

    if active:
        conn.close()
        return "busy"

    cursor.execute("""
        UPDATE rides 
        SET status='Accepted', driver_id=?
        WHERE id=?
    """, (driver_id, ride_id))

    cursor.execute("""
        UPDATE driver
        SET is_busy=1, current_ride_id=?
        WHERE id=?
    """, (ride_id, driver_id))

    conn.commit()
    conn.close()
    return "accepted"


def get_all_rides():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM rides ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_pending_rides_for_driver(driver_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT is_busy FROM driver WHERE id=?", (driver_id,))
    is_busy = cursor.fetchone()[0]

    if is_busy == 1:
        cursor.execute("""
            SELECT id, passenger_id, pickup, destination, fare, status,
                   driver_id, scheduled_date, scheduled_time
            FROM rides
            WHERE driver_id=? AND status IN ('Assigned', 'Accepted')
        """, (driver_id,))
    else:
        cursor.execute("""
            SELECT id, passenger_id, pickup, destination, fare, status,
                   driver_id, scheduled_date, scheduled_time
            FROM rides
            WHERE status IN ('Requested', 'Scheduled')
        """)

    rows = cursor.fetchall()
    conn.close()
    return rows



def driver_reject_ride(ride_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE rides
        SET status='Rejected'
        WHERE id=?
    """, (ride_id,))
    conn.commit()
    conn.close()


def complete_ride(ride_id, driver_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE rides
        SET status='Completed'
        WHERE id=?
    """, (ride_id,))

    cursor.execute("""
        UPDATE driver
        SET is_busy=0,
            current_ride_id=NULL
        WHERE id=?
    """, (driver_id,))

    conn.commit()
    conn.close()
    
def admin_assign_driver(ride_id, driver_id):
   conn = sqlite3.connect(DB_NAME)
   cursor = conn.cursor()

   cursor.execute("""
        UPDATE rides
        SET driver_id=?, status='Accepted',
            assigned_by_admin=1
        WHERE id=?
    """, (driver_id, ride_id))
 
   cursor.execute("""
        UPDATE driver
        SET is_busy=1, current_ride_id=?
        WHERE id=?
    """, (ride_id, driver_id))

   conn.commit()
   conn.close()
   return True




def get_passenger_id_from_ride_id(ride_id):
    """Additive function to get passenger_id from ride_id"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT passenger_id FROM rides WHERE id=?", (ride_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def insert_admin_assignment_notifications(ride_id, driver_id, passenger_id):
    """Additive function to insert admin assignment notifications (no existing code changes)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO driver_notifications (driver_id, ride_id, message)
    VALUES (?, ?, ?)
    """, (driver_id, ride_id, f"You have been assigned to ride #{ride_id} by admin"))

    cursor.execute("""
    INSERT INTO passenger_notifications (passenger_id, ride_id, message)
    VALUES (?, ?, ?)
    """, (passenger_id, ride_id, f"Your ride #{ride_id} has been assigned a driver by admin"))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
    print("Database initialized!")
