import sqlite3

def migrate_database():
    """Add wind_surfers column and visited_at to ratings table"""
    conn = sqlite3.connect('crag_data.db')
    cursor = conn.cursor()
    
    # Check if wind_surfers column exists
    cursor.execute("PRAGMA table_info(ratings)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'wind_surfers' not in columns:
        print("Adding wind_surfers column...")
        cursor.execute("""
            ALTER TABLE ratings 
            ADD COLUMN wind_surfers INTEGER DEFAULT 0
        """)
        print("✓ Added wind_surfers column")
    
    if 'visited_at' not in columns:
        print("Adding visited_at column...")
        cursor.execute("""
            ALTER TABLE ratings 
            ADD COLUMN visited_at TEXT
        """)
        print("✓ Added visited_at column")
    
    conn.commit()
    conn.close()
    print("\n✓ Database migration complete!")

if __name__ == "__main__":
    migrate_database()