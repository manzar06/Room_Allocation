"""
Script to initialize blocks in the database
This ensures blocks exist even if the database was already created
"""

from app import app, db, Block, Room

def init_blocks():
    with app.app_context():
        db.create_all()
        
        # Get or create blocks
        blocks_to_create = [
            {'name': 'Block A', 'gender': 'male', 'description': 'Boys Hostel Block A'},
            {'name': 'Block B', 'gender': 'female', 'description': 'Girls Hostel Block B'},
            {'name': 'Block C', 'gender': 'male', 'description': 'Boys Hostel Block C'},
            {'name': 'Block D', 'gender': 'female', 'description': 'Girls Hostel Block D'},
        ]
        
        created_blocks = []
        for block_data in blocks_to_create:
            existing_block = Block.query.filter_by(name=block_data['name']).first()
            if not existing_block:
                block = Block(**block_data)
                db.session.add(block)
                created_blocks.append(block_data['name'])
            else:
                print(f"Block {block_data['name']} already exists")
        
        if created_blocks:
            db.session.commit()
            print(f"Created blocks: {', '.join(created_blocks)}")
        else:
            print("All blocks already exist")
        
        # Create empty rooms for blocks that don't have any rooms
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
                print(f"Created 5 rooms for {block.name}")
        
        if rooms_created:
            db.session.commit()
            print("Created sample empty rooms for blocks that didn't have any")
        else:
            print("All blocks already have rooms")
        
        # Display all blocks
        all_blocks = Block.query.all()
        print(f"\nTotal blocks in database: {len(all_blocks)}")
        for block in all_blocks:
            room_count = Room.query.filter_by(block_id=block.id).count()
            print(f"  - {block.name} ({block.gender}): {room_count} rooms")

if __name__ == '__main__':
    init_blocks()

