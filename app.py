import mysql.connector
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "student_portal"

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="aswin11",
    database="student_portal"
)

cursor = db.cursor(dictionary=True)
print("Database Connected Successfully")

# ---------------- HOME ----------------


@app.route('/')
def home():
    return render_template('index.html')

# ---------------- STUDENT LOGIN ----------------


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        reg_no = request.form['reg_no']
        password = request.form['password']

        cursor.execute("""
            SELECT * FROM students 
            WHERE reg_no=%s AND password=%s
        """, (reg_no, password))

        student = cursor.fetchone()

        print("LOGIN RESULT:", student)

        if student:

            session.clear()
            session['reg_no'] = student['reg_no']
            session['name'] = student['name']

            return redirect('/dashboard')

        return "Invalid Login"

    return render_template('login.html')

# ---------------- DASHBOARD ----------------


@app.route('/dashboard')
def dashboard():

    # 👇 ADD THIS LINE HERE
    print("DASHBOARD SESSION:", session.get('reg_no'))

    if 'reg_no' not in session:
        return redirect('/login')

    reg_no = session['reg_no']

    cursor.execute("""
        SELECT * FROM students WHERE reg_no=%s
    """, (reg_no,))
    student = cursor.fetchone()

    cursor.execute("""
        SELECT subject, marks FROM marks WHERE reg_no=%s
    """, (reg_no,))
    marks = cursor.fetchall()

    return render_template(
        'dashboard.html',
        student=student,
        marks=marks,
        name=student['name']
    )

# ---------------- PROFILE ----------------


@app.route('/profile')
def profile():

    print("PROFILE SESSION:", session.get('reg_no'))

    if 'reg_no' not in session:
        return redirect('/login')

    cursor.execute("""
        SELECT * FROM students WHERE reg_no=%s
    """, (session['reg_no'],))

    student = cursor.fetchone()

    return render_template('profile.html', student=student)

# ---------------- ANNOUNCEMENTS (STUDENT) ----------------


@app.route('/announcements')
def announcements():

    if 'reg_no' not in session:
        return redirect('/login')

    cursor.execute("SELECT * FROM announcements ORDER BY created_at DESC")
    data = cursor.fetchall()

    return render_template('announcements.html', announcements=data)

# ---------------- ADD STUDENT (ADMIN) ----------------


@app.route('/add_student', methods=['GET', 'POST'])
def add_student():

    if 'admin' not in session:
        return redirect('/admin_login')

    if request.method == 'POST':

        try:
            reg_no = request.form['reg_no']
            name = request.form['name']
            email = request.form['email']
            department = request.form['department']
            year = request.form['year']
            phone = request.form['phone']
            password = request.form['password']

            cursor.execute("""
                INSERT INTO students
                (reg_no, name, email, department, year, phone, password)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (reg_no, name, email, department, year, phone, password))

            db.commit()

            return redirect('/add_student?success=1')

        except Exception as e:
            return f"Error: {e}"

    return render_template('admin/add_student.html')
# ---------------- ADMIN LOGIN (MISSING FIX ADDED) ----------------


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        if username == "admin" and password == "admin123":
            session['admin'] = True
            return redirect('/admin_dashboard')

        return "Invalid Admin Login"

    return render_template('admin/admin_login.html')

# ---------------- ADMIN DASHBOARD ----------------


@app.route('/admin_dashboard')
def admin_dashboard():

    if 'admin' not in session:
        return redirect('/admin_login')

    cursor.execute("SELECT COUNT(*) AS total FROM students")
    total_students = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(DISTINCT department) AS total FROM students")
    total_departments = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM announcements")
    total_announcements = cursor.fetchone()['total']

    return render_template(
        'admin/admin_dashboard.html',
        total_students=total_students,
        total_departments=total_departments,
        total_announcements=total_announcements
    )
# ---------------- MARKS (STUDENT) ----------------


@app.route('/marks')
def marks():

    if 'reg_no' not in session:
        return redirect('/login')

    cursor.execute("""
        SELECT subject, marks
        FROM marks
        WHERE reg_no=%s
    """, (session['reg_no'],))

    data = cursor.fetchall()

    return render_template('marks.html', marks=data)

# ---------------- ADD MARKS (ADMIN) ----------------


@app.route('/add_marks', methods=['GET', 'POST'])
def add_marks():

    if 'admin' not in session:
        return redirect('/admin_login')

    if request.method == 'POST':
        try:
            reg_no = request.form.get('reg_no')
            subject = request.form.get('subject')
            marks = request.form.get('marks')

            # validation
            if not reg_no or not subject or not marks:
                return "Missing form data"

            cursor.execute("""
                INSERT INTO marks (reg_no, subject, marks)
                VALUES (%s, %s, %s)
            """, (reg_no, subject, marks))

            db.commit()

            return redirect('/add_marks?success=1')

        except Exception as e:
            return f"Error: {e}"

    return render_template('admin/add_marks.html')

# ---------------- ADD ANNOUNCEMENT (ADMIN) ----------------


@app.route('/add_announcement', methods=['GET', 'POST'])
def add_announcement():

    try:
        if 'admin' not in session:
            return redirect('/admin_login')

        if request.method == 'POST':

            title = request.form['title']
            description = request.form['description']

            cursor.execute("""
                INSERT INTO announcements (title, description)
                VALUES (%s, %s)
            """, (title, description))

            db.commit()

            return redirect('/add_announcement?success=1')

        return render_template('admin/add_announcement.html')

    except Exception as e:
        print("ANNOUNCEMENT ERROR:", e)
        return f"Something went wrong: {e}"

# ---------------- ATTENDANCE (PLACEHOLDER) ----------------


@app.route('/attendance')
def attendance():

    if 'reg_no' not in session:
        return redirect('/login')

    reg_no = session['reg_no']

    cursor.execute("""
        SELECT total_classes, attended_classes 
        FROM attendance 
        WHERE reg_no=%s
    """, (reg_no,))

    data = cursor.fetchone()

    attendance_percentage = 0

    if data and data['total_classes'] > 0:
        attendance_percentage = round(
            (data['attended_classes'] / data['total_classes']) * 100, 2
        )

    return render_template(
        'attendance.html',
        data=data,
        percentage=attendance_percentage
    )


@app.route('/add_attendance', methods=['GET', 'POST'])
def add_attendance():

    try:
        if 'admin' not in session:
            return redirect('/admin_login')

        if request.method == 'POST':

            reg_no = request.form['reg_no']
            total_classes = request.form['total_classes']
            attended_classes = request.form['attended_classes']

            cursor.execute("""
                INSERT INTO attendance (reg_no, total_classes, attended_classes)
                VALUES (%s, %s, %s)
            """, (reg_no, total_classes, attended_classes))

            db.commit()

            return redirect('/add_attendance?success=1')

        return render_template('admin/add_attendance.html')

    except Exception as e:
        print("ERROR IN ADD ATTENDANCE:", e)
        return f"Something went wrong: {e}"

# ---------------- LOGOUT ----------------


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ---------------- RUN APP ----------------
if __name__ == '__main__':
    app.run(debug=True, port=5001)
