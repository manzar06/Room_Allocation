# Smart Hostel Room Allocation System

A comprehensive web-based platform for automating hostel room allocation and management. This system replaces manual processes with a digital solution for students and administrators.

## Features

### Student Module
- User registration and login
- Apply for hostel room with preferences
- View available rooms and occupancy status
- Track application status
- Submit and track complaints (electricity, water, cleaning, etc.)
- View fee records and payment status

### Admin Module
- Admin login and dashboard
- Manage hostel blocks, floors, and rooms
- View real-time room availability
- Approve/reject student applications
- Manual room allocation
- Handle and respond to student complaints
- Generate reports and statistics

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite (SQLAlchemy ORM)
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Flask-Login

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python app.py
   ```

3. **Access the application:**
   - Open your browser and go to: `http://localhost:5000`

## Database Setup

The database (`hostel.db`) will be automatically created when you first run the application. The database includes the following tables:

- **User**: Stores student and admin accounts
- **Block**: Hostel blocks (male/female)
- **Room**: Individual rooms with capacity and occupancy
- **Application**: Student room applications
- **Allocation**: Room assignments to students
- **Complaint**: Student complaints and their status
- **Fee**: Fee records and payment tracking

## Creating an Admin Account

To create an admin account, you can either:

1. Register normally and manually update the database:
   ```python
   from app import app, db, User
   with app.app_context():
       user = User.query.filter_by(username='your_username').first()
       user.role = 'admin'
       db.session.commit()
   ```

2. Or use Python shell:
   ```python
   python
   >>> from app import app, db, User
   >>> from werkzeug.security import generate_password_hash
   >>> with app.app_context():
   ...     admin = User(
   ...         username='admin',
   ...         email='admin@hostel.com',
   ...         password_hash=generate_password_hash('admin123'),
   ...         full_name='Admin User',
   ...         role='admin'
   ...     )
   ...     db.session.add(admin)
   ...     db.session.commit()
   ```

## Usage

### For Students:
1. Register an account
2. Login to your dashboard
3. Apply for a room
4. View available rooms
5. Submit complaints if needed
6. Check fee status

### For Administrators:
1. Login with admin credentials
2. Manage blocks and rooms
3. Review and approve/reject applications
4. Handle complaints
5. View reports and statistics

## Project Structure

```
project_1/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── hostel.db             # SQLite database (created automatically)
├── templates/            # HTML templates
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
        └── style.css     # Stylesheet
```

## Security Notes

- Change the `SECRET_KEY` in `app.py` before deploying to production
- Use a production-ready database (PostgreSQL) for deployment
- Implement additional security measures (CSRF protection, rate limiting)
- Use environment variables for sensitive configuration

## License

This project is created for educational purposes.

