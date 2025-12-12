from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import csv
import io

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
    checkout_reason = db.Column(db.Text, nullable=True)
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
    if application.preferred_room_type and room.room_type:
        if application.preferred_room_type.lower() != room.room_type.lower():
            flash('Room type does not match student preference', 'error')
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
    
    # Auto-generate hostel fee when room is allocated
    fee = Fee(
        student_id=application.student_id,
        amount=room.price if room.price else 5000,  # Use room price or default
        fee_type='hostel_fee',
        due_date=datetime.utcnow() + timedelta(days=30)  # Due in 30 days
    )
    db.session.add(fee)
    
    db.session.commit()
    flash('Application approved and room allocated! Hostel fee generated.', 'success')
    return redirect(url_for('manage_applications'))

@app.route('/admin/application/<int:app_id>/auto_allocate', methods=['POST'])
@login_required
def auto_allocate_application(app_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    
    application = Application.query.get_or_404(app_id)
    
    # Prevent duplicate allocation
    existing_allocation = Allocation.query.filter_by(student_id=application.student_id, status='active').first()
    if existing_allocation:
        flash('Student already has an active allocation', 'error')
        return redirect(url_for('manage_applications'))
    
    student = application.student
    
    # Build query for available rooms
    query = Room.query.join(Block).filter(
        Room.current_occupancy < Room.capacity
    )
    
    # Filter by gender (required)
    if student.gender:
        query = query.filter(Block.gender == student.gender)
    
    # Filter by preferred block if specified
    if application.preferred_block:
        query = query.filter(Block.name == application.preferred_block)
    
    # Filter by preferred room type if specified
    if application.preferred_room_type:
        query = query.filter(Room.room_type == application.preferred_room_type)
    
    # Order by: prefer rooms with lower occupancy, then by room number
    room = query.order_by(Room.current_occupancy.asc(), Room.room_number.asc()).first()
    
    if not room:
        flash('No available room matching student preferences. Please assign manually.', 'error')
        return redirect(url_for('manage_applications'))
    
    # Create allocation
    allocation = Allocation(
        student_id=application.student_id,
        room_id=room.id,
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
    application.admin_notes = f'Auto-allocated to {room.block.name} - Floor {room.floor} - Room {room.room_number}'
    
    # Auto-generate hostel fee
    fee = Fee(
        student_id=application.student_id,
        amount=room.price if room.price else 5000,
        fee_type='hostel_fee',
        due_date=datetime.utcnow() + timedelta(days=30)
    )
    db.session.add(fee)
    
    db.session.commit()
    flash(f'Auto-allocated to {room.block.name} - Floor {room.floor} - Room {room.room_number}!', 'success')
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
    
    status_filter = request.args.get('status', 'all')
    if status_filter == 'active':
        allocations = Allocation.query.filter_by(status='active').all()
    elif status_filter == 'checked_out':
        allocations = Allocation.query.filter_by(status='checked_out').all()
    else:
        allocations = Allocation.query.all()
    
    return render_template('admin/allocations.html', allocations=allocations, status_filter=status_filter)

@app.route('/admin/allocation/<int:alloc_id>/check_in', methods=['POST'])
@login_required
def process_check_in(alloc_id):
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    allocation = Allocation.query.get_or_404(alloc_id)
    check_in_date_str = request.form.get('check_in_date')
    
    if check_in_date_str:
        allocation.check_in_date = datetime.strptime(check_in_date_str, '%Y-%m-%d')
    else:
        allocation.check_in_date = datetime.utcnow()
    
    db.session.commit()
    flash('Check-in processed successfully!', 'success')
    return redirect(url_for('view_allocations'))

@app.route('/admin/allocation/<int:alloc_id>/check_out', methods=['POST'])
@login_required
def process_check_out(alloc_id):
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    allocation = Allocation.query.get_or_404(alloc_id)
    check_out_date_str = request.form.get('check_out_date')
    checkout_reason = request.form.get('checkout_reason', '')
    checkout_reason_other = request.form.get('checkout_reason_other', '')
    
    if check_out_date_str:
        allocation.check_out_date = datetime.strptime(check_out_date_str, '%Y-%m-%d')
    else:
        allocation.check_out_date = datetime.utcnow()
    
    allocation.status = 'checked_out'
    # Combine reason with other notes if provided
    if checkout_reason == 'Other' and checkout_reason_other:
        allocation.checkout_reason = f"Other: {checkout_reason_other}"
    else:
        allocation.checkout_reason = checkout_reason
    
    # Free up the room
    room = allocation.room
    room.current_occupancy = max(room.current_occupancy - 1, 0)
    if room.current_occupancy < room.capacity:
        room.status = 'available'
    
    db.session.commit()
    flash('Check-out processed successfully! Room is now available.', 'success')
    return redirect(url_for('view_allocations'))

@app.route('/admin/reports')
@login_required
def reports():
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    # Room statistics
    total_students = User.query.filter_by(role='student').count()
    total_rooms = Room.query.count()
    occupied_rooms = Room.query.filter(Room.current_occupancy > 0).count()
    available_rooms = Room.query.filter_by(status='available').count()
    
    # Fee statistics
    total_fees = Fee.query.count()
    paid_fees = Fee.query.filter_by(status='paid').count()
    pending_fees = Fee.query.filter_by(status='pending').count()
    total_collected = db.session.query(db.func.sum(Fee.amount)).filter_by(status='paid').scalar() or 0
    total_pending = db.session.query(db.func.sum(Fee.amount)).filter_by(status='pending').scalar() or 0
    
    # Overdue fees (due date passed but not paid)
    from datetime import datetime
    overdue_fees = Fee.query.filter(
        Fee.status == 'pending',
        Fee.due_date < datetime.utcnow()
    ).count()
    total_overdue = db.session.query(db.func.sum(Fee.amount)).filter(
        Fee.status == 'pending',
        Fee.due_date < datetime.utcnow()
    ).scalar() or 0
    
    # Allocation statistics
    active_allocations = Allocation.query.filter_by(status='active').count()
    checked_out = Allocation.query.filter_by(status='checked_out').count()
    
    return render_template('admin/reports.html',
                         total_students=total_students,
                         total_rooms=total_rooms,
                         occupied_rooms=occupied_rooms,
                         available_rooms=available_rooms,
                         total_fees=total_fees,
                         paid_fees=paid_fees,
                         pending_fees=pending_fees,
                         total_collected=total_collected,
                         total_pending=total_pending,
                         overdue_fees=overdue_fees,
                         total_overdue=total_overdue,
                         active_allocations=active_allocations,
                         checked_out=checked_out)

@app.route('/admin/reports/export/students')
@login_required
def export_students_csv():
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Student ID', 'Full Name', 'Username', 'Email', 'Gender', 'Phone', 'Registration Date'])
    
    # Data
    students = User.query.filter_by(role='student').all()
    for student in students:
        writer.writerow([
            student.student_id or '',
            student.full_name,
            student.username,
            student.email,
            student.gender or '',
            student.phone or '',
            student.created_at.strftime('%Y-%m-%d') if student.created_at else ''
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=students_report.csv'}
    )

@app.route('/admin/reports/export/fees')
@login_required
def export_fees_csv():
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Student Name', 'Student ID', 'Fee Type', 'Amount', 'Due Date', 'Paid Date', 'Status', 'Receipt Number', 'Payment Method'])
    
    # Data
    fees = Fee.query.join(User).order_by(Fee.due_date.desc()).all()
    for fee in fees:
        writer.writerow([
            fee.student.full_name,
            fee.student.student_id or '',
            fee.fee_type,
            fee.amount,
            fee.due_date.strftime('%Y-%m-%d') if fee.due_date else '',
            fee.paid_date.strftime('%Y-%m-%d') if fee.paid_date else '',
            fee.status,
            fee.receipt_number or '',
            fee.payment_method or ''
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=fees_report.csv'}
    )

@app.route('/admin/reports/export/allocations')
@login_required
def export_allocations_csv():
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Student Name', 'Student ID', 'Block', 'Floor', 'Room Number', 'Room Type', 'Allocated Date', 'Check-in Date', 'Check-out Date', 'Status', 'Check-out Reason'])
    
    # Data
    allocations = Allocation.query.join(User).join(Room).join(Block).order_by(Allocation.allocated_at.desc()).all()
    for alloc in allocations:
        writer.writerow([
            alloc.student.full_name,
            alloc.student.student_id or '',
            alloc.room.block.name,
            alloc.room.floor,
            alloc.room.room_number,
            alloc.room.room_type or '',
            alloc.allocated_at.strftime('%Y-%m-%d') if alloc.allocated_at else '',
            alloc.check_in_date.strftime('%Y-%m-%d') if alloc.check_in_date else '',
            alloc.check_out_date.strftime('%Y-%m-%d') if alloc.check_out_date else '',
            alloc.status,
            alloc.checkout_reason or ''
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=allocations_report.csv'}
    )

@app.route('/admin/reports/export/rooms')
@login_required
def export_rooms_csv():
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Block', 'Gender', 'Floor', 'Room Number', 'Room Type', 'Capacity', 'Current Occupancy', 'Status', 'Price'])
    
    # Data
    rooms = Room.query.join(Block).order_by(Block.name, Room.floor, Room.room_number).all()
    for room in rooms:
        writer.writerow([
            room.block.name,
            room.block.gender,
            room.floor,
            room.room_number,
            room.room_type or '',
            room.capacity,
            room.current_occupancy,
            room.status,
            room.price or ''
        ])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=rooms_report.csv'}
    )

@app.route('/admin/reports/export/summary')
@login_required
def export_summary_csv():
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Summary statistics
    total_students = User.query.filter_by(role='student').count()
    total_rooms = Room.query.count()
    occupied_rooms = Room.query.filter(Room.current_occupancy > 0).count()
    available_rooms = Room.query.filter_by(status='available').count()
    total_fees = Fee.query.count()
    paid_fees = Fee.query.filter_by(status='paid').count()
    pending_fees = Fee.query.filter_by(status='pending').count()
    total_collected = db.session.query(db.func.sum(Fee.amount)).filter_by(status='paid').scalar() or 0
    total_pending = db.session.query(db.func.sum(Fee.amount)).filter_by(status='pending').scalar() or 0
    active_allocations = Allocation.query.filter_by(status='active').count()
    checked_out = Allocation.query.filter_by(status='checked_out').count()
    
    writer.writerow(['Report Type', 'Value'])
    writer.writerow(['Total Students', total_students])
    writer.writerow(['Total Rooms', total_rooms])
    writer.writerow(['Occupied Rooms', occupied_rooms])
    writer.writerow(['Available Rooms', available_rooms])
    writer.writerow(['Active Allocations', active_allocations])
    writer.writerow(['Checked Out', checked_out])
    writer.writerow(['Total Fees', total_fees])
    writer.writerow(['Paid Fees', paid_fees])
    writer.writerow(['Pending Fees', pending_fees])
    writer.writerow(['Total Collected (Rs)', total_collected])
    writer.writerow(['Total Pending (Rs)', total_pending])
    writer.writerow(['Report Generated', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')])
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=summary_report.csv'}
    )

@app.route('/admin/fees', methods=['GET', 'POST'])
@login_required
def manage_fees():
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        amount = float(request.form.get('amount'))
        fee_type = request.form.get('fee_type')
        due_date_str = request.form.get('due_date')
        
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        
        fee = Fee(
            student_id=student_id,
            amount=amount,
            fee_type=fee_type,
            due_date=due_date
        )
        db.session.add(fee)
        db.session.commit()
        flash('Fee created successfully!', 'success')
        return redirect(url_for('manage_fees'))
    
    fees = Fee.query.order_by(Fee.due_date.desc()).all()
    students = User.query.filter_by(role='student').all()
    return render_template('admin/fees.html', fees=fees, students=students)

@app.route('/admin/fee/<int:fee_id>/mark_paid', methods=['POST'])
@login_required
def mark_fee_paid(fee_id):
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    fee = Fee.query.get_or_404(fee_id)
    fee.status = 'paid'
    fee.paid_date = datetime.utcnow()
    fee.receipt_number = request.form.get('receipt_number')
    fee.payment_method = request.form.get('payment_method', 'cash')
    
    db.session.commit()
    flash('Fee marked as paid!', 'success')
    return redirect(url_for('manage_fees'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Initialize default blocks - check each one individually
        default_blocks = [
            {'name': 'Block A', 'gender': 'male', 'description': 'Boys Hostel Block A'},
            {'name': 'Block B', 'gender': 'female', 'description': 'Girls Hostel Block B'},
            {'name': 'Block C', 'gender': 'male', 'description': 'Boys Hostel Block C'},
            {'name': 'Block D', 'gender': 'female', 'description': 'Girls Hostel Block D'},
        ]
        
        created_blocks = []
        for block_data in default_blocks:
            existing_block = Block.query.filter_by(name=block_data['name']).first()
            if not existing_block:
                block = Block(**block_data)
                db.session.add(block)
                created_blocks.append(block_data['name'])
        
        if created_blocks:
            db.session.commit()
            print(f"Initialized default blocks: {', '.join(created_blocks)}")
        
        # Initialize empty rooms for blocks that don't have any rooms
        blocks = Block.query.all()
        rooms_created = False
        for block in blocks:
            existing_rooms = Room.query.filter_by(block_id=block.id).count()
            if existing_rooms == 0:
                # Add a few empty rooms on floor 1 for this block
                for room_num in ['101', '102', '103', '104', '105']:
                    room = Room(
                        block_id=block.id,
                        floor=1,
                        room_number=room_num,
                        capacity=2,
                        room_type='AC' if int(room_num[-1]) % 2 == 1 else 'Non-AC',
                        price=5000 if int(room_num[-1]) % 2 == 1 else 3500,
                        current_occupancy=0,
                        status='available'
                    )
                    db.session.add(room)
                rooms_created = True
        
        if rooms_created:
            db.session.commit()
            print("Initialized sample empty rooms for blocks that didn't have any")
    
    app.run(debug=True)

