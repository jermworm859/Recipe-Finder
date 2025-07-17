import sqlite3

conn = sqlite3.connect('favorites.db')
cursor = conn.cursor()

# Add 'notes' column if it doesn't exist
cursor.execute("ALTER TABLE favorites ADD COLUMN notes TEXT")

conn.commit()
conn.close()

print("Notes column added.")