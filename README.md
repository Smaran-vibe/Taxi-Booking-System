# Taxi Booking System

A desktop-based Taxi Booking System developed using Python and CustomTkinter, designed to simulate real-world ride booking and management operations.  
The system supports multiple user roles including Passenger, Driver, and Admin with integrated route calculation and database management.



## Key Features

### Passenger Panel
- Book rides with pickup and drop locations  
- Automatic fare calculation  
- Route distance estimation  
- Ride scheduling  

### Driver Panel
- View assigned rides  
- Manage ride status  
- Trip tracking functionality  

### Admin Panel
- Manage passengers and drivers  
- Monitor ride activity  
- Database management controls  



## API Integration

- Integrated OSRM (Open Source Routing Machine) API  
- Real-time route calculation  
- Distance and estimated travel computation  
- Enhances realistic ride-booking functionality  



## Technologies Used

- Python  
- CustomTkinter (GUI Framework)  
- MySQL / SQLite (Database)  
- REST API Integration (OSRM)  



## System Architecture

The application follows a modular structure:
- GUI Layer (CustomTkinter)  
- Business Logic Layer  
- Database Layer  
- External Routing API Integration  



## How to Run

1. Install required Python dependencies  
2. Configure database connection  
3. Run the main Python file  

```bash
python main.py
