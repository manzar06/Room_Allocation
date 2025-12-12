"""
Script to create an admin account for the Hostel Management System
Run this script to create an admin user.
"""

from app import app, db, User
from werkzeug.security import generate_password_hash

def create_admin():
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("Admin user already exists!")
            return
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@hostel.com',
            password_hash=generate_password_hash('admin123'),
            full_name='System Administrator',
            role='admin',
            phone='0000000000'
        )
        
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")
        print("Username: admin")
        print("Password: admin123")
        print("\nPlease change the password after first login!")

if __name__ == '__main__':
    create_admin()

