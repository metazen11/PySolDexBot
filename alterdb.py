import sqlite3

def add_is_new_column():
    conn = sqlite3.connect('raydium_pools.db')
    c = conn.cursor()

    # Check if the is_new column exists
    c.execute("PRAGMA table_info(pools);")
    columns = [column[1] for column in c.fetchall()]
    if 'is_new' not in columns:
        # Add the is_new column
        c.execute('ALTER TABLE pools ADD COLUMN is_new INTEGER DEFAULT 0')
        print("Added is_new column to pools table.")
    else:
        print("is_new column already exists.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_is_new_column()
