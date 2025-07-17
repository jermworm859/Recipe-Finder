import sqlite3

conn = sqlite3.connect('favorites.db')
cursor = conn.cursor()

cursor.execute('''
    ALTER TABLE favorites ADD COLUMN ingredients TEXT               
''')

conn.commit()
conn.close()