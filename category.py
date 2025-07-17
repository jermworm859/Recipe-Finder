import sqlite3

conn = sqlite3.connect('favorites.db')
cursor = conn.cursor()

cursor.execute("ALTER TABLE favorites ADD COLUMN category TEXT")
cursor.execute("ALTER TABLE favorites ADD COLUMN area TEXT")

conn.commit()
conn.close()

print("Added category and area columns to favorites")