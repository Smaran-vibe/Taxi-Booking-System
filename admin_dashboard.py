import customtkinter as ctk
from tkinter import ttk, messagebox
import subprocess
import sys
from admin_data import (
    get_total_users,
    get_total_bookings,
    get_total_payments,
    admin_get_all_bookings,
    admin_get_scheduled_bookings,
    admin_get_all_users,
    admin_get_all_payments,
    admin_get_all_drivers_with_ratings
)


def logout(window=None):
    if window:
        try:
            window.destroy()
        except:
            pass
    subprocess.Popen(["python", "main.py"])
    sys.exit(0)


BG_MAIN = "#0D1323"
BG_SIDEBAR = "#0F1630"
CARD_BG = "#121522"
TEXT_MAIN = "#AFC3FF"
GLOW = "#5C5CFF"
ACCENT = "#4A3AFF"
HEADER = "#E8EDFF"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.geometry("1200x700")
app.title("Admin Dashboard")
app.configure(bg=BG_MAIN)


style = ttk.Style()
style.theme_use("clam")

style.configure(
    "Treeview",
    background=BG_MAIN,
    fieldbackground=BG_MAIN,
    foreground="white",
    rowheight=32,
    bordercolor=CARD_BG,
    font=("Arial", 11)
)

style.configure(
    "Treeview.Heading",
    background=BG_SIDEBAR,
    foreground="white",
    font=("Arial", 12, "bold"),
    relief="flat"
)

style.map(
    "Treeview",
    background=[("selected", GLOW)],
    foreground=[("selected", "black")]
)


style.configure(
    "Vertical.TScrollbar",
    background=BG_SIDEBAR,
    troughcolor=BG_MAIN,
    arrowcolor="white"
)


sidebar = ctk.CTkFrame(app, width=220, corner_radius=0, fg_color=BG_SIDEBAR)
sidebar.pack(side="left", fill="y")

title = ctk.CTkLabel(sidebar, text="Admin Panel",
                     font=("Arial", 20, "bold"), text_color=HEADER)
title.pack(pady=22)

# Active button management
active_button = None


def activate(btn):
    global active_button
    if active_button and active_button is not btn:

        try:
            active_button.configure(
                fg_color=BG_SIDEBAR, border_width=1, border_color=BG_SIDEBAR)
        except Exception:
            pass

    try:
        btn.configure(fg_color=ACCENT, border_width=2, border_color=GLOW)
    except Exception:
        pass


def show_drivers():
    clear_main()

    header = ctk.CTkLabel(main, text="All Drivers", font=(
        "Arial", 24, "bold"), text_color=HEADER)
    header.pack(pady=(20, 8), anchor="w", padx=24)

    wrapper, tree = create_table(
        main, ("ID", "Name", "Phone", "Rating"), height=14)

    try:
        drivers = admin_get_all_drivers_with_ratings()
        for d in drivers:

            formatted_driver = list(d)
            if formatted_driver[3] is not None:
                formatted_driver[3] = f"{formatted_driver[3]:.2f}"
            else:
                formatted_driver[3] = "N/A"
            tree.insert("", "end", values=formatted_driver)
    except Exception as e:
        print(f"Error fetching drivers: {e}")


def show_all_bookings():
    clear_main()

    header = ctk.CTkLabel(main, text="All Bookings", font=(
        "Arial", 24, "bold"), text_color=HEADER)
    header.pack(pady=(20, 8), anchor="w", padx=24)

    wrapper, tree = create_table(main, ("ID", "Passenger", "Pickup", "Destination",
                                 "Status", "Fare", "Scheduled Date", "Scheduled Time"), height=14)

    try:
        bookings = admin_get_all_bookings()
        for b in bookings:

            tree.insert("", "end", values=b)
    except Exception as e:
        print(f"Error fetching all bookings: {e}")


def show_all_passengers():
    clear_main()

    header = ctk.CTkLabel(main, text="All Passengers", font=(
        "Arial", 24, "bold"), text_color=HEADER)
    header.pack(pady=(20, 8), anchor="w", padx=24)

    wrapper, tree = create_table(
        main, ("User ID", "Name", "Email", "Phone"), height=14)

    try:
        passengers = admin_get_all_users()
        for p in passengers:
            tree.insert("", "end", values=p)
    except Exception as e:
        print(f"Error fetching all passengers: {e}")


def make_button(text, command):
    return ctk.CTkButton(
        sidebar,
        text=text,
        width=180,
        corner_radius=10,
        fg_color=BG_SIDEBAR,
        hover_color="#1A2340",
        border_color=BG_SIDEBAR,
        border_width=1,
        command=command
    )


btn_dashboard = make_button(
    "Dashboard", lambda: [activate(btn_dashboard), show_dashboard()])
btn_users = make_button("Users", lambda: [activate(btn_users), show_users()])
btn_bookings = make_button(
    "Bookings", lambda: [activate(btn_bookings), show_bookings()])
btn_payments = make_button(
    "Payments", lambda: [activate(btn_payments), show_payments()])

btn_dashboard.pack(pady=12)
btn_users.pack(pady=12)
btn_bookings.pack(pady=12)
btn_payments.pack(pady=12)

btn_drivers = make_button(
    "Drivers", lambda: [activate(btn_drivers), show_drivers()])
btn_drivers.pack(pady=12)

btn_all_bookings = make_button("All Bookings", lambda: [
                               activate(btn_all_bookings), show_all_bookings()])
btn_all_bookings.pack(pady=12)

btn_all_passengers = make_button("All Passengers", lambda: [
                                 activate(btn_all_passengers), show_all_passengers()])
btn_all_passengers.pack(pady=12)

logout_btn = ctk.CTkButton(sidebar, text="Logout", fg_color="#B30000",
                           hover_color="#7A0000", width=180, corner_radius=8,
                           command=lambda: logout(app))
logout_btn.pack(side="bottom", pady=22)


#  MAIN CONTENT

main = ctk.CTkFrame(app, fg_color=BG_MAIN)
main.pack(side="right", fill="both", expand=True)


def clear_main():
    for widget in main.winfo_children():
        widget.destroy()


def create_table(parent, columns, height=14):
    # wrapper with card look
    wrapper = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=12,
                           border_color=GLOW, border_width=2)
    wrapper.pack(fill="both", expand=True, padx=20, pady=12)

    #  ttk Treeview
    tree = ttk.Treeview(wrapper, columns=columns,
                        show="headings", height=height, selectmode="browse")

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=140)

    # vertical scrollbar
    vsb = ttk.Scrollbar(wrapper, orient="vertical",
                        command=tree.yview, style="Vertical.TScrollbar")
    tree.configure(yscrollcommand=vsb.set)

    tree.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=12)
    vsb.pack(side="right", fill="y", padx=(0, 12), pady=12)

    return wrapper, tree


#  DASHBOARD PAGE

def show_dashboard():
    clear_main()

    header = ctk.CTkLabel(main, text="Dashboard", font=(
        "Arial", 26, "bold"), text_color=HEADER)
    header.pack(pady=(18, 8), anchor="w", padx=24)

    # Cards row
    cards_frame = ctk.CTkFrame(main, fg_color=BG_MAIN)
    cards_frame.pack(fill="x", pady=(6, 12), padx=12)

    def glowing_card(parent, title, value, color):
        box = ctk.CTkFrame(parent, width=220, height=120,
                           corner_radius=14, fg_color=CARD_BG,
                           border_color=GLOW, border_width=2)
        box.pack(side="left", padx=18, pady=10)
        ctk.CTkLabel(box, text=title, font=("Arial", 13, "bold"),
                     text_color="#9FB0FF").pack(pady=(14, 4))
        ctk.CTkLabel(box, text=value, font=(
            "Arial", 26, "bold"), text_color=color).pack()

    try:
        total_users = get_total_users()
    except Exception:
        total_users = "—"
    try:
        total_bookings = get_total_bookings()
    except Exception:
        total_bookings = "—"
    try:
        total_pay = get_total_payments()
        clean_pay = f"{total_pay:.2f}"
    except Exception:
        clean_pay = "—"

    glowing_card(cards_frame, "Total Users", f"{total_users}", "#6C9BFF")
    glowing_card(cards_frame, "Total Bookings", f"{total_bookings}", "#65FFB2")
    glowing_card(cards_frame, "Total Payments", f"NPR {clean_pay}", "#FFD27F")

    ctk.CTkLabel(main, text="Recent Bookings", font=("Arial", 20, "bold"),
                 text_color=TEXT_MAIN).pack(pady=(10, 6), anchor="w", padx=24)

    wrapper, tree = create_table(
        main, ("ID", "Passenger", "Pickup", "Destination", "Status", "Fare"), height=12)

    # Fill table
    try:
        rows = admin_get_all_bookings()
        for r in rows:
            \
            tree.insert("", "end", values=r)
    except Exception:
        pass

    ctk.CTkLabel(main, text="Scheduled Bookings", font=("Arial", 20, "bold"),
                 text_color=TEXT_MAIN).pack(pady=(20, 6), anchor="w", padx=24)

    wrapper, tree = create_table(main, ("ID", "Passenger", "Pickup", "Destination",
                                 "Status", "Fare", "Scheduled Date", "Scheduled Time"), height=8)

    try:
        scheduled_rows = admin_get_scheduled_bookings()
        if not scheduled_rows:

            ctk.CTkLabel(wrapper, text="No scheduled bookings found",
                         text_color="#AFC3FF", font=("Arial", 12)).pack(pady=20)
        else:
            for r in scheduled_rows:

                tree.insert("", "end", values=r)
    except Exception as e:
        print(f"Scheduled bookings error: {e}")


def show_users():
    clear_main()

    header = ctk.CTkLabel(main, text="Users List", font=(
        "Arial", 24, "bold"), text_color=HEADER)
    header.pack(pady=(20, 8), anchor="w", padx=24)

    wrapper, tree = create_table(
        main, ("User ID", "Name", "Email", "Phone"), height=14)

    # Fill users
    try:
        users = admin_get_all_users()
        for u in users:
            # expected tuple (id, name, email, phone) or similar
            tree.insert("", "end", values=u)
    except Exception:
        pass


def show_bookings():
    clear_main()

    header = ctk.CTkLabel(main, text="All Bookings", font=(
        "Arial", 24, "bold"), text_color=HEADER)
    header.pack(pady=(20, 8), anchor="w", padx=24)

    # Add driver list fetch for assignment
    def get_all_drivers():
        import sqlite3
        conn = sqlite3.connect("taxi_booking.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM driver WHERE is_busy=0")
        drivers = cursor.fetchall()
        conn.close()
        return drivers

    # Assign driver popup
    def assign_driver_popup(ride_id):
        popup = ctk.CTkToplevel(app)
        popup.title("Assign Driver")
        popup.geometry("300x200")
        popup.resizable(False, False)

        ctk.CTkLabel(popup, text=f"Assign Driver to Ride #{ride_id}", font=(
            "Arial", 14)).pack(pady=10)

        drivers = get_all_drivers()
        if not drivers:
            ctk.CTkLabel(popup, text="No available drivers",
                         text_color="red").pack(pady=20)
            return

        driver_var = ctk.StringVar(value=drivers[0][0])
        driver_dropdown = ctk.CTkOptionMenu(
            popup, values=[f"{d[0]} - {d[1]}" for d in drivers], variable=driver_var)
        driver_dropdown.pack(pady=10, padx=20, fill="x")

        def confirm_assignment():
            selected_driver_id = int(driver_var.get().split(" - ")[0])
            from database import admin_assign_driver, get_passenger_id_from_ride_id, insert_admin_assignment_notifications
            if admin_assign_driver(ride_id, selected_driver_id):
                passenger_id = get_passenger_id_from_ride_id(ride_id)
                if passenger_id:
                    insert_admin_assignment_notifications(
                        ride_id, selected_driver_id, passenger_id)
                messagebox.showinfo("Success", "Driver assigned successfully")
                popup.destroy()
                show_bookings()  # Refresh table
            else:
                messagebox.showerror("Error", "Failed to assign driver")

        ctk.CTkButton(popup, text="Assign", fg_color=ACCENT,
                      command=confirm_assignment).pack(pady=10, padx=20, fill="x")

    wrapper = ctk.CTkFrame(main, fg_color=CARD_BG,
                           corner_radius=12, border_color=GLOW, border_width=2)
    wrapper.pack(fill="both", expand=True, padx=20, pady=12)

    columns = ("ID", "Passenger", "Pickup", "Destination", "Status",
               "Fare", "Scheduled Date", "Scheduled Time", "Action")
    tree = ttk.Treeview(wrapper, columns=columns,
                        show="headings", height=14, selectmode="browse")

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=140)
    tree.column("Action", width=100)

    vsb = ttk.Scrollbar(wrapper, orient="vertical",
                        command=tree.yview, style="Vertical.TScrollbar")
    tree.configure(yscrollcommand=vsb.set)

    tree.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=12)
    vsb.pack(side="right", fill="y", padx=(0, 12), pady=12)

    assign_selected_btn = ctk.CTkButton(main, text="Assign Driver to Selected Ride", fg_color=ACCENT, hover_color=GLOW,
                                        command=lambda: assign_driver_for_selected_ride())
    assign_selected_btn.pack(pady=10, padx=20, fill="x")

    def assign_driver_for_selected_ride():
        selected_item = tree.focus()
        if selected_item:
            ride_id = tree.item(selected_item)['values'][0]
            status = tree.item(selected_item)['values'][4]
            if status == "Requested":
                assign_driver_popup(ride_id)
            else:
                messagebox.showinfo(
                    "Info", f"Cannot assign driver. Ride status is '{status}'. Only 'Requested' rides can be assigned.")
        else:
            messagebox.showinfo(
                "Info", "Please select a ride from the table to assign a driver.")

    try:
        bookings = admin_get_all_bookings()
        for b in bookings:
            ride_id = b[0]
            status = b[4]
            # Add empty action cell placeholder

            row_values = list(b) + [""]
            item_id = tree.insert("", "end", values=row_values)

            if status == "Requested":
                assign_btn = ctk.CTkButton(wrapper, text="Assign", fg_color=ACCENT, hover_color=GLOW,
                                           width=80, command=lambda rid=ride_id: assign_driver_popup(rid))

    except Exception:
        pass


#  PAYMENTS PAGE

def show_payments():
    clear_main()

    header = ctk.CTkLabel(main, text="Payments History", font=(
        "Arial", 24, "bold"), text_color=HEADER)
    header.pack(pady=(20, 8), anchor="w", padx=24)

    wrapper, tree = create_table(
        main, ("Payment ID", "Ride ID", "Passenger", "Amount", "Date"), height=14)

    try:
        payments = admin_get_all_payments()
        for p in payments:
            tree.insert("", "end", values=p)
    except Exception:
        pass


def _admin_refresh_status():
    try:

        if active_button and hasattr(active_button, 'text'):
            page = active_button.text.lower()
            if 'dashboard' in page:
                show_dashboard()
            elif 'users' in page:
                show_users()
            elif 'bookings' in page:
                show_bookings()
            elif 'payments' in page:
                show_payments()
    except Exception as e:
        print(f"Polling error: {e}")

    app.after(5000, _admin_refresh_status)


activate(btn_dashboard)
show_dashboard()

_admin_refresh_status()

app.mainloop()
