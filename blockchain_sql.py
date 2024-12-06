import sqlite3
import json

class SQLDatabase:
    def __init__(self, db_name="blocks.db"):
        # Connect to the database and create a cursor
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        # Create a table to store block data
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocks (
                height_key INTEGER PRIMARY KEY,   -- Ensures uniqueness of height_key
                type TEXT,
                hash TEXT,
                height INTEGER,
                messages TEXT,                   -- Stores JSON string of the messages array
                minedBy TEXT,
                nonce TEXT,
                timestamp INTEGER
            )
        ''')
        self.conn.commit()

    def add_block(self, block_obj):
        # Prepare the block data for insertion
        height_key = block_obj["height_key"]
        block_type = block_obj["type"]
        block_hash = block_obj["hash"]
        height = block_obj["height"]
        messages = json.dumps(block_obj["messages"])  # Serialize messages list as JSON
        mined_by = block_obj["minedBy"]
        nonce = block_obj["nonce"]
        timestamp = block_obj["timestamp"]

        try:
            # Insert the block data, ensure uniqueness with height_key
            self.cursor.execute('''
                INSERT INTO blocks (height_key, type, hash, height, messages, minedBy, nonce, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (height_key, block_type, block_hash, height, messages, mined_by, nonce, timestamp))
            self.conn.commit()
            print(f"Block with height_key {height_key} added successfully.")
        except sqlite3.IntegrityError:
            print(f"Block with height_key {height_key} already exists. Duplicate not added.")

    def close(self):
        # Close the database connection
        self.conn.close()