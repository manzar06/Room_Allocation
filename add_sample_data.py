"""
Script to add sample blocks and rooms to the database
Run this to populate the database with initial data
"""

from app import app, db, Block, Room

def add_sample_data():
    with app.app_context():
        db.create_all()
        
        # Add blocks if they don't exist
        if not Block.query.first():
            block_a = Block(name='Block A', gender='male', description='Boys Hostel Block A')
            block_b = Block(name='Block B', gender='female', description='Girls Hostel Block B')
            db.session.add(block_a)
            db.session.add(block_b)
            db.session.commit()
            print("Added Block A (Male) and Block B (Female)")
        else:
            print("Blocks already exist")
        
        # Add rooms if they don't exist
        if not Room.query.first():
            block_a = Block.query.filter_by(name='Block A').first()
            block_b = Block.query.filter_by(name='Block B').first()
            
            if block_a:
                rooms_a = [
                    Room(block_id=block_a.id, floor=1, room_number='101', capacity=2, room_type='AC', price=5000),
                    Room(block_id=block_a.id, floor=1, room_number='102', capacity=2, room_type='Non-AC', price=3500),
                    Room(block_id=block_a.id, floor=1, room_number='103', capacity=3, room_type='AC', price=6000),
                    Room(block_id=block_a.id, floor=2, room_number='201', capacity=2, room_type='AC', price=5000),
                    Room(block_id=block_a.id, floor=2, room_number='202', capacity=2, room_type='Non-AC', price=3500),
                ]
                db.session.add_all(rooms_a)
            
            if block_b:
                rooms_b = [
                    Room(block_id=block_b.id, floor=1, room_number='101', capacity=2, room_type='AC', price=5200),
                    Room(block_id=block_b.id, floor=1, room_number='102', capacity=2, room_type='Non-AC', price=3600),
                    Room(block_id=block_b.id, floor=2, room_number='201', capacity=2, room_type='AC', price=5200),
                ]
                db.session.add_all(rooms_b)
            
            db.session.commit()
            print("Added sample rooms")
        else:
            print("Rooms already exist")
        
        print("\nSample data added successfully!")
        print("You can now:")
        print("1. View blocks in Admin - Blocks")
        print("2. View rooms in Admin - Rooms")
        print("3. Students can see rooms in View Rooms")

if __name__ == '__main__':
    add_sample_data()

