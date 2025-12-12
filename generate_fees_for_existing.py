"""
Script to generate fees for students who already have room allocations
but don't have fees yet
"""

from app import app, db, User, Allocation, Fee, Room
from datetime import datetime, timedelta

def generate_fees_for_existing():
    with app.app_context():
        # Get all active allocations
        allocations = Allocation.query.filter_by(status='active').all()
        
        fees_created = 0
        fees_skipped = 0
        
        for allocation in allocations:
            student = allocation.student
            room = allocation.room
            
            # Check if student already has a pending hostel fee
            existing_fee = Fee.query.filter_by(
                student_id=student.id,
                fee_type='hostel_fee',
                status='pending'
            ).first()
            
            if existing_fee:
                print(f"Skipping {student.username} - already has pending fee")
                fees_skipped += 1
                continue
            
            # Create fee based on room price
            amount = room.price if room.price else 5000
            due_date = datetime.utcnow() + timedelta(days=30)
            
            fee = Fee(
                student_id=student.id,
                amount=amount,
                fee_type='hostel_fee',
                due_date=due_date
            )
            
            db.session.add(fee)
            fees_created += 1
            print(f"Created fee for {student.username} - Amount: Rs{amount}, Room: {room.block.name} {room.room_number}")
        
        db.session.commit()
        print(f"\nSummary:")
        print(f"Fees created: {fees_created}")
        print(f"Fees skipped (already exist): {fees_skipped}")

if __name__ == '__main__':
    generate_fees_for_existing()

