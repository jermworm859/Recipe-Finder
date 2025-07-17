import sqlite3

conn = sqlite3.connect('favorites.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        meal_id TEXT UNIQUE,
        meal_name TEXT,
        meal_thumb TEXT
    )
''')

conn.commit()
conn.close()