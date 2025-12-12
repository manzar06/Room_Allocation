Smart Hostel Room Allocation System

A web-based platform for automating hostel room allocation and management. This system replaces manual processes with a digital solution for students and administrators.

Features

Student Module
- User registration and login
- Apply for hostel room with preferences
- View available rooms and occupancy status
- Track application status
- Submit and track complaints like electricity, water, cleaning, and more
- View fee records and payment status

Admin Module
- Admin login and dashboard
- Manage hostel blocks, floors, and rooms
- View real-time room availability
- Approve or reject student applications
- Manual room allocation
- Handle and respond to student complaints
- Generate reports and statistics

Technology Stack

- Backend: Flask using Python
- Database: SQLite with SQLAlchemy ORM
- Frontend: HTML, CSS, JavaScript
- Authentication: Flask-Login

Installation

1. Install dependencies:
   On Windows, use: python -m pip install -r requirements.txt
   On Mac or Linux, use: pip install -r requirements.txt

2. Run the application:
   python app.py

3. Access the application:
   Open your browser and go to http://localhost:5000

Database Setup

The database file called hostel.db will be automatically created when you first run the application. The database includes the following tables:

- User: Stores student and admin accounts
- Block: Hostel blocks for male or female students
- Room: Individual rooms with capacity and occupancy information
- Application: Student room applications
- Allocation: Room assignments to students
- Complaint: Student complaints and their status
- Fee: Fee records and payment tracking

Creating an Admin Account

To create an admin account, you can use the init_admin.py script:

1. First, make sure the database is created by running the app once:
   python app.py
   Then stop it and run:
   python init_admin.py

This will create an admin account with:
- Username: admin
- Password: admin123

Please change the password after your first login.

Alternatively, you can create an admin account manually using Python:

python
from app import app, db, User
from werkzeug.security import generate_password_hash
with app.app_context():
    admin = User(
        username='admin',
        email='admin@hostel.com',
        password_hash=generate_password_hash('admin123'),
        full_name='Admin User',
        role='admin'
    )
    db.session.add(admin)
    db.session.commit()

Initializing Blocks and Rooms

To set up default blocks and rooms in the database, run:

python init_blocks.py

This will create default blocks (Block A, Block B, Block C, Block D) and some sample rooms.

Usage

For Students:
1. Register an account with your details
2. Login to your dashboard
3. Apply for a room by selecting your preferred block and room type
4. View available rooms to see what's open
5. Submit complaints if you have any issues
6. Check your fee status and payment records

For Administrators:
1. Login with your admin credentials
2. Manage blocks and rooms from the admin dashboard
3. Review and approve or reject student applications
4. Handle student complaints and respond to them
5. View reports and statistics about room allocations

Project Structure

Room_Allocation/
├── app.py                 Main Flask application
├── requirements.txt       Python dependencies
├── hostel.db             SQLite database (created automatically)
├── init_admin.py         Script to create admin account
├── init_blocks.py         Script to initialize blocks and rooms
├── add_sample_data.py     Script to add sample data
├── templates/            HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── student/
│   │   ├── dashboard.html
│   │   ├── apply.html
│   │   ├── rooms.html
│   │   ├── complaints.html
│   │   └── fees.html
│   └── admin/
│       ├── dashboard.html
│       ├── applications.html
│       ├── blocks.html
│       ├── rooms.html
│       ├── complaints.html
│       ├── allocations.html
│       └── reports.html
└── static/
    └── css/
        └── style.css     Stylesheet

