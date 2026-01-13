import sqlite3

DB = 'database.db'

def migrate():
    db = sqlite3.connect(DB)
    cur = db.cursor()

    # Create students and trainers tables if they don't exist
    cur.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS trainers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Populate from users table
    cur.execute("SELECT id, username, role FROM users WHERE role='student'")
    students = cur.fetchall()
    for s in students:
        try:
            cur.execute('INSERT OR IGNORE INTO students (user_id) VALUES (?)', (s[0],))
        except Exception:
            pass

    cur.execute("SELECT id, username, role FROM users WHERE role='trainer'")
    trainers = cur.fetchall()
    for t in trainers:
        try:
            cur.execute('INSERT OR IGNORE INTO trainers (user_id) VALUES (?)', (t[0],))
        except Exception:
            pass

    db.commit()
    db.close()
    print('Migration complete: students:', len(students), 'trainers:', len(trainers))

if __name__ == '__main__':
    migrate()