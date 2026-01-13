from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, make_response
import sqlite3, qrcode, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "vtars_secret"

DB = "database.db"

def get_db():
    return sqlite3.connect(DB)


# ---------------- LOGIN ----------------
@app.route("/admin-login", methods=["GET", "POST"], endpoint='login')
def login():
    if request.method == "POST":
        print("✅ POST received")

        # Normalize inputs to avoid leading/trailing whitespace issues
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        print("Username:", repr(username))
        print("Password:", repr(password))

        db = get_db()
        cur = db.cursor()
        cur.execute(
            "SELECT id, role, vtc_id FROM users WHERE username=? AND password=?",
            (username, password)
        )
        user = cur.fetchone()
        db.close()

        print("DB user:", user)

        if user:
            session["user_id"] = user[0]
            session["role"] = user[1]
            session["vtc_id"] = user[2]
            session["username"] = username

            print("🔁 Redirecting based on role:", user[1])

            if user[1] == "admin":
                return redirect(url_for("admin"))
            else:
                return redirect(url_for("dashboard"))
        else:
            print("❌ Invalid credentials")
            flash("Invalid credentials")
            return redirect(url_for("login"))

    # If someone is already logged in but not admin, don't show the admin login page
    if "user_id" in session and session.get("role") != "admin":
        flash("Access restricted to Admin users.")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/")
def portals():
    # Redirect logged-in users to their dashboard
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("portals.html")


# ---------------- USER LOGIN FOR STUDENTS/TRAINERS ----------------
@app.route("/user-login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        role = (request.form.get("role") or "").strip()
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()

        print("User login attempt:", role, repr(username))

        db = get_db()
        cur = db.cursor()
        cur.execute(
            "SELECT id, role, vtc_id FROM users WHERE username=? AND password=? AND role=?",
            (username, password, role)
        )
        user = cur.fetchone()
        db.close()

        if user:
            session["user_id"] = user[0]
            session["role"] = user[1]
            session["vtc_id"] = user[2]
            session["username"] = username
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials for selected role")
            return redirect(url_for("user_login"))

    return render_template("user_login.html")


# ---------------- STUDENT LOGIN ----------------
@app.route('/student-login', methods=['GET','POST'])
def student_login():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = (request.form.get('password') or '').strip()

        db = get_db()
        cur = db.cursor()
        cur.execute(
            "SELECT id, role, vtc_id FROM users WHERE username=? AND password=? AND role='student'",
            (username, password)
        )
        user = cur.fetchone()
        db.close()

        if user:
            session['user_id'] = user[0]
            session['role'] = user[1]
            session['vtc_id'] = user[2]
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid student credentials')
            return redirect(url_for('student_login'))

    return render_template('student_login.html')


# ---------------- TRAINER LOGIN ----------------
@app.route('/trainer-login', methods=['GET','POST'])
def trainer_login():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = (request.form.get('password') or '').strip()

        db = get_db()
        cur = db.cursor()
        cur.execute(
            "SELECT id, role, vtc_id FROM users WHERE username=? AND password=? AND role='trainer'",
            (username, password)
        )
        user = cur.fetchone()
        db.close()

        if user:
            session['user_id'] = user[0]
            session['role'] = user[1]
            session['vtc_id'] = user[2]
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid trainer credentials')
            return redirect(url_for('trainer_login'))

    return render_template('trainer_login.html')
 

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    # Preserve role so we can redirect to the correct portal after clearing session
    role = session.get("role")
    session.clear()
    flash("You have been logged out.")

    if role == "admin":
        return redirect(url_for("login"))
    elif role == "student":
        return redirect(url_for("student_login"))
    elif role == "trainer":
        return redirect(url_for("trainer_login"))
    else:
        return redirect(url_for("user_login"))


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    today = datetime.now().strftime("%Y-%m-%d")
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM attendance WHERE date=?",
        (today,)
    )
    count = cur.fetchone()[0]

    username = session.get("username")
    reported = False
    reported_time = None

    if session.get("role") != "admin":
        cur.execute(
            "SELECT time FROM attendance WHERE user_id=? AND date=?",
            (session["user_id"], today)
        )
        row = cur.fetchone()
        if row:
            reported = True
            reported_time = row[0]

    db.close()

    return render_template(
        "dashboard.html",
        count=count,
        role=session["role"],
        username=username,
        reported=reported,
        reported_time=reported_time
    )


# ---------------- ADMIN: DAILY QR ----------------
@app.route("/admin")
def admin():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if session.get("role") != "admin":
        flash("Access denied: admin only")
        return redirect(url_for("dashboard"))

    vtc_id = session["vtc_id"]
    today = datetime.now().strftime("%Y-%m-%d")

    db = get_db()
    cur = db.cursor()
    # Create a new QR session for today
    cur.execute(
        "INSERT INTO qr_sessions (vtc_id, date, active) VALUES (?, ?, 1)",
        (vtc_id, today)
    )
    qr_id = cur.lastrowid
    db.commit()

    qr_data = f"QRSESSION:{qr_id}"
    img = qrcode.make(qr_data)

    os.makedirs("static/qr", exist_ok=True)
    path = f"static/qr/{qr_id}.png"
    img.save(path)

    # Ensure there is only one QR session per day for this vtc
    cur.execute("SELECT id FROM qr_sessions WHERE date=? AND vtc_id=? LIMIT 1", (today, vtc_id))
    existing = cur.fetchone()
    if existing:
        qr_id = existing[0]
        path = f"static/qr/{qr_id}.png"
        if not os.path.exists(path):
            img = qrcode.make(f"QRSESSION:{qr_id}")
            os.makedirs("static/qr", exist_ok=True)
            img.save(path)
    else:
        cur.execute(
            "INSERT INTO qr_sessions (vtc_id, date, active) VALUES (?, ?, 1)",
            (vtc_id, today)
        )
        qr_id = cur.lastrowid
        db.commit()

        qr_data = f"QRSESSION:{qr_id}"
        img = qrcode.make(qr_data)

        os.makedirs("static/qr", exist_ok=True)
        path = f"static/qr/{qr_id}.png"
        img.save(path)

    # Fetch today's attendance report
    cur.execute(
        "SELECT a.id, u.username, a.time FROM attendance a JOIN users u ON a.user_id=u.id WHERE a.date=? ORDER BY a.time",
        (today,)
    )
    attendance = cur.fetchall()

    # Count
    cur.execute(
        "SELECT COUNT(*) FROM attendance WHERE date=?",
        (today,)
    )
    count = cur.fetchone()[0]

    # Fetch trainers and students separately with reported flag
    cur.execute(
        "SELECT u.id, u.username, CASE WHEN a.id IS NOT NULL THEN 1 ELSE 0 END as reported FROM users u JOIN trainers t ON t.user_id=u.id LEFT JOIN attendance a ON a.user_id=u.id AND a.date=? ORDER BY u.username",
        (today,)
    )
    trainers = cur.fetchall()

    cur.execute(
        "SELECT u.id, u.username, CASE WHEN a.id IS NOT NULL THEN 1 ELSE 0 END as reported FROM users u JOIN students s ON s.user_id=u.id LEFT JOIN attendance a ON a.user_id=u.id AND a.date=? ORDER BY u.username",
        (today,)
    )
    students = cur.fetchall()

    db.close()

    return render_template("admin.html", qr=path, attendance=attendance, count=count, trainers=trainers, students=students)

# ---------------- SCAN QR ----------------
@app.route("/scan", methods=["GET", "POST"])
def scan():
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Only students and trainers can scan
    if session.get("role") == "admin":
        return redirect(url_for("admin"))

    if request.method == "POST":
        qr_raw = (request.form.get("qr") or "").strip()

        # Accept formats: 'QRSESSION:12' or '12'
        if not qr_raw:
            return jsonify({"status": "error", "message": "Missing QR data"})

        if qr_raw.isdigit():
            qr_id = qr_raw
        elif qr_raw.startswith("QRSESSION:"):
            qr_id = qr_raw.split(":", 1)[1]
        else:
            return jsonify({"status": "error", "message": "Invalid QR code"})

        user_id = session["user_id"]
        today = datetime.now().strftime("%Y-%m-%d")
        time = datetime.now().strftime("%H:%M:%S")

        db = get_db()
        cur = db.cursor()

        # 1️⃣ Check QR session is valid and active for today
        cur.execute("""
            SELECT id FROM qr_sessions 
            WHERE id=? AND date=? AND active=1
        """, (qr_id, today))
        qr_session = cur.fetchone()

        if not qr_session:
            return jsonify({"status": "error", "message": "QR code expired or invalid"})

        # 2️⃣ Prevent double attendance
        cur.execute("""
            SELECT id FROM attendance 
            WHERE user_id=? AND date=?
        """, (user_id, today))

        if cur.fetchone():
            return jsonify({"status": "error", "message": "Attendance already marked today"})

        # 3️⃣ Record attendance
        cur.execute("""
            INSERT INTO attendance (user_id, qr_session_id, date, time)
            VALUES (?, ?, ?, ?)
        """, (user_id, qr_id, today, time))
        cur.execute(
            "UPDATE qr_sessions SET active=0 WHERE date <> ?",
            (today,)
        )

        db.commit()

        return jsonify({"status": "success", "message": "✅ Attendance marked successfully"})

    return render_template("scan.html", role=session.get("role"), username=session.get("username"))


# ---------------- ADMIN: REPORT EXPORT ----------------
@app.route('/admin/send_report', methods=['POST'])
def send_report():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if session.get("role") != "admin":
        flash("Access denied: admin only")
        return redirect(url_for("dashboard"))

    today = datetime.now().strftime("%Y-%m-%d")
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "SELECT u.username, u.role, u.vtc_id, a.qr_session_id, a.date, a.time FROM attendance a JOIN users u ON a.user_id=u.id WHERE a.date=? ORDER BY a.time",
        (today,)
    )
    rows = cur.fetchall()
    db.close()

    # Build CSV
    import io, csv
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['username','role','vtc_id','qr_session_id','date','time'])
    for r in rows:
        writer.writerow(r)

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=attendance_{today}.csv"
    output.headers["Content-Type"] = "text/csv"
    return output



# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
