from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hostel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student' or 'admin'
    gender = db.Column(db.String(10), nullable=True)  # 'male' or 'female'
    full_name = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.String(50), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    applications = db.relationship('Application', backref='student', lazy=True)
    complaints = db.relationship('Complaint', backref='student', lazy=True)
    fees = db.relationship('Fee', backref='student', lazy=True)
    allocation = db.relationship('Allocation', backref='student', uselist=False, lazy=True)

class Block(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    gender = db.Column(db.String(10), nullable=False)  # 'male' or 'female'
    description = db.Column(db.Text, nullable=True)
    rooms = db.relationship('Room', backref='block', lazy=True)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    block_id = db.Column(db.Integer, db.ForeignKey('block.id'), nullable=False)
    floor = db.Column(db.Integer, nullable=False)
    room_number = db.Column(db.String(20), nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=2)
    current_occupancy = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='available')  # 'available', 'occupied', 'maintenance'
    room_type = db.Column(db.String(50), nullable=True)  # 'AC', 'Non-AC', etc.
    price = db.Column(db.Float, nullable=True)
    
    allocations = db.relationship('Allocation', backref='room', lazy=True)
    
    __table_args__ = (db.UniqueConstraint('block_id', 'floor', 'room_number', name='unique_room'),)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    preferred_block = db.Column(db.String(50), nullable=True)
    preferred_room_type = db.Column(db.String(50), nullable=True)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)

class Allocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    allocated_at = db.Column(db.DateTime, default=datetime.utcnow)
    check_in_date = db.Column(db.DateTime, nullable=True)
    check_out_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='active')  # 'active', 'checked_out'

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 'electricity', 'water', 'cleaning', etc.
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='open')  # 'open', 'in_progress', 'resolved', 'closed'
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    admin_response = db.Column(db.Text, nullable=True)
    assigned_to = db.Column(db.String(100), nullable=True)

class Fee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    fee_type = db.Column(db.String(50), nullable=False)  # 'hostel_fee', 'maintenance', etc.
    due_date = db.Column(db.DateTime, nullable=False)
    paid_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'paid', 'overdue'
    receipt_number = db.Column(db.String(50), unique=True, nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        student_id = request.form.get('student_id')
        phone = request.form.get('phone')
        role = request.form.get('role', 'student')
        gender = request.form.get('gender')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('register'))
        
        if role == 'student' and User.query.filter_by(student_id=student_id).first():
            flash('Student ID already exists', 'error')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            full_name=full_name,
            student_id=student_id,
            phone=phone,
            role=role,
            gender=gender
        )
        
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# Student Routes
@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    application = Application.query.filter_by(student_id=current_user.id).first()
    allocation = Allocation.query.filter_by(student_id=current_user.id).first()
    complaints = Complaint.query.filter_by(student_id=current_user.id).order_by(Complaint.submitted_at.desc()).limit(5).all()
    pending_fees = Fee.query.filter_by(student_id=current_user.id, status='pending').all()
    
    return render_template('student/dashboard.html', 
                         application=application, 
                         allocation=allocation,
                         complaints=complaints,
                         pending_fees=pending_fees)

@app.route('/student/apply', methods=['GET', 'POST'])
@login_required
def apply_for_room():
    if current_user.role != 'student':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    if Application.query.filter_by(student_id=current_user.id).first():
        flash('You have already submitted an application', 'info')
        return redirect(url_for('student_dashboard'))
    
    if request.method == 'POST':
        application = Application(
            student_id=current_user.id,
            preferred_block=request.form.get('preferred_block'),
            preferred_room_type=request.form.get('preferred_room_type'),
            reason=request.form.get('reason')
        )
        db.session.add(application)
        db.session.commit()
        flash('Application submitted successfully!', 'success')
        return redirect(url_for('student_dashboard'))
    
    blocks = Block.query.filter_by(gender=current_user.gender).all()
    return render_template('student/apply.html', blocks=blocks)

@app.route('/student/rooms')
@login_required
def view_rooms():
    if current_user.role != 'student':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    blocks = Block.query.filter_by(gender=current_user.gender).all()
    rooms_data = []
    for block in blocks:
        rooms = Room.query.filter_by(block_id=block.id).all()
        rooms_data.append({
            'block': block,
            'rooms': rooms
        })
    
    return render_template('student/rooms.html', rooms_data=rooms_data)

@app.route('/student/complaints', methods=['GET', 'POST'])
@login_required
def complaints():
    if current_user.role != 'student':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        complaint = Complaint(
            student_id=current_user.id,
            category=request.form.get('category'),
            title=request.form.get('title'),
            description=request.form.get('description')
        )
        db.session.add(complaint)
        db.session.commit()
        flash('Complaint submitted successfully!', 'success')
        return redirect(url_for('complaints'))
    
    complaints_list = Complaint.query.filter_by(student_id=current_user.id).order_by(Complaint.submitted_at.desc()).all()
    return render_template('student/complaints.html', complaints=complaints_list)

@app.route('/student/fees')
@login_required
def student_fees():
    if current_user.role != 'student':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    fees = Fee.query.filter_by(student_id=current_user.id).order_by(Fee.due_date.desc()).all()
    return render_template('student/fees.html', fees=fees)

# Admin Routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    total_students = User.query.filter_by(role='student').count()
    total_rooms = Room.query.count()
    available_rooms = Room.query.filter_by(status='available').count()
    pending_applications = Application.query.filter_by(status='pending').count()
    open_complaints = Complaint.query.filter_by(status='open').count()
    
    recent_applications = Application.query.order_by(Application.applied_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_students=total_students,
                         total_rooms=total_rooms,
                         available_rooms=available_rooms,
                         pending_applications=pending_applications,
                         open_complaints=open_complaints,
                         recent_applications=recent_applications)

@app.route('/admin/blocks', methods=['GET', 'POST'])
@login_required
def manage_blocks():
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        block = Block(
            name=request.form.get('name'),
            gender=request.form.get('gender'),
            description=request.form.get('description')
        )
        db.session.add(block)
        db.session.commit()
        flash('Block added successfully!', 'success')
        return redirect(url_for('manage_blocks'))
    
    blocks = Block.query.all()
    return render_template('admin/blocks.html', blocks=blocks)

@app.route('/admin/rooms', methods=['GET', 'POST'])
@login_required
def manage_rooms():
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        room = Room(
            block_id=request.form.get('block_id'),
            floor=request.form.get('floor'),
            room_number=request.form.get('room_number'),
            capacity=request.form.get('capacity'),
            room_type=request.form.get('room_type'),
            price=request.form.get('price', 0)
        )
        db.session.add(room)
        db.session.commit()
        flash('Room added successfully!', 'success')
        return redirect(url_for('manage_rooms'))
    
    blocks = Block.query.all()
    rooms = Room.query.all()
    return render_template('admin/rooms.html', blocks=blocks, rooms=rooms)

@app.route('/admin/applications')
@login_required
def manage_applications():
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    applications = Application.query.order_by(Application.applied_at.desc()).all()
    available_rooms = Room.query.join(Block).filter(Room.current_occupancy < Room.capacity).all()
    return render_template('admin/applications.html', applications=applications, available_rooms=available_rooms)

@app.route('/admin/application/<int:app_id>/approve', methods=['POST'])
@login_required
def approve_application(app_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    application = Application.query.get_or_404(app_id)
    room_id = request.form.get('room_id')
    
    if not room_id:
        flash('Please select a room', 'error')
        return redirect(url_for('manage_applications'))
    
    # Prevent duplicate allocation for the same student
    existing_allocation = Allocation.query.filter_by(student_id=application.student_id, status='active').first()
    if existing_allocation:
        flash('Student already has an active allocation', 'error')
        return redirect(url_for('manage_applications'))
    
    room = Room.query.get(room_id)
    if room.block.gender and application.student.gender and room.block.gender != application.student.gender:
        flash('Room gender does not match student gender', 'error')
        return redirect(url_for('manage_applications'))
    if room.current_occupancy >= room.capacity:
        flash('Room is full', 'error')
        return redirect(url_for('manage_applications'))
    
    # Create allocation
    allocation = Allocation(
        student_id=application.student_id,
        room_id=room_id,
        check_in_date=datetime.utcnow()
    )
    db.session.add(allocation)
    
    # Update room occupancy
    room.current_occupancy += 1
    if room.current_occupancy >= room.capacity:
        room.status = 'occupied'
    
    # Update application
    application.status = 'approved'
    application.reviewed_at = datetime.utcnow()
    application.admin_notes = request.form.get('notes', '')
    
    db.session.commit()
    flash('Application approved and room allocated!', 'success')
    return redirect(url_for('manage_applications'))

@app.route('/admin/application/<int:app_id>/reject', methods=['POST'])
@login_required
def reject_application(app_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    application = Application.query.get_or_404(app_id)
    application.status = 'rejected'
    application.reviewed_at = datetime.utcnow()
    application.admin_notes = request.form.get('notes', '')
    
    db.session.commit()
    flash('Application rejected', 'info')
    return redirect(url_for('manage_applications'))

@app.route('/admin/complaints')
@login_required
def admin_complaints():
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    complaints = Complaint.query.order_by(Complaint.submitted_at.desc()).all()
    return render_template('admin/complaints.html', complaints=complaints)

@app.route('/admin/complaint/<int:complaint_id>/update', methods=['POST'])
@login_required
def update_complaint(complaint_id):
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    complaint = Complaint.query.get_or_404(complaint_id)
    complaint.status = request.form.get('status')
    complaint.admin_response = request.form.get('admin_response')
    complaint.assigned_to = request.form.get('assigned_to')
    
    if complaint.status == 'resolved':
        complaint.resolved_at = datetime.utcnow()
    
    db.session.commit()
    flash('Complaint updated successfully!', 'success')
    return redirect(url_for('admin_complaints'))

@app.route('/admin/allocations')
@login_required
def view_allocations():
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    allocations = Allocation.query.filter_by(status='active').all()
    return render_template('admin/allocations.html', allocations=allocations)

@app.route('/admin/reports')
@login_required
def reports():
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    total_students = User.query.filter_by(role='student').count()
    total_rooms = Room.query.count()
    occupied_rooms = Room.query.filter(Room.current_occupancy > 0).count()
    available_rooms = Room.query.filter_by(status='available').count()
    
    return render_template('admin/reports.html',
                         total_students=total_students,
                         total_rooms=total_rooms,
                         occupied_rooms=occupied_rooms,
                         available_rooms=available_rooms)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

