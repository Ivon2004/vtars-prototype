import sqlite3

db = sqlite3.connect('database.db')
cur = db.cursor()
cur.execute("UPDATE users SET password=? WHERE username=?", ('1234','Ivon'))
db.commit()
print('Updated rows:', cur.rowcount)
db.close()
