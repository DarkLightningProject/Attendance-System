from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, date
import os
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from sqlalchemy import or_

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

# ---------- AUTH ----------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)  # In real app, hash this

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('students_list'))
        else:
            message = 'Invalid credentials!'
    return render_template('login.html', message=message)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ---------- MODELS ----------
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    time_added = db.Column(db.DateTime, default=datetime.utcnow)
    attendances = db.relationship(
        'Attendance',
        backref='student',
        lazy=True,
        cascade="all, delete-orphan"
    )

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.String(20), nullable=False)  # 'YYYY-MM-DD'
    status = db.Column(db.String(10), nullable=False, default="Pending")  # Present/Absent

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)

class Holiday(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)  # Changed from String to Date
    description = db.Column(db.String(100), nullable=True)
# ---------- ROUTES ----------
@app.route('/')
def home():
    return render_template('home.html')

# --- Student API ---
@app.route('/students', methods=['POST'])
def add_student():
    data = request.get_json()
    name = data.get('name')
    roll_number = data.get('roll_number')
    email = data.get('email')
    if not name or not roll_number or not email:
        return jsonify({'error': 'Missing data'}), 400
    if Student.query.filter((Student.roll_number == roll_number) | (Student.email == email)).first():
        return jsonify({'error': 'Student with this roll number or email already exists'}), 400
    student = Student(name=name, roll_number=roll_number, email=email)
    db.session.add(student)
    db.session.commit()
    return jsonify({'message': 'Student added successfully', 'id': student.id}), 201

@app.route('/students', methods=['GET'])
def get_students():
    students = Student.query.all()
    return jsonify([
        {
            'id': s.id,
            'name': s.name,
            'roll_number': s.roll_number,
            'email': s.email,
            'time_added': s.time_added.strftime('%Y-%m-%d %H:%M:%S')
        }
        for s in students
    ])

@app.route('/students/<int:id>', methods=['PUT'])
def update_student(id):
    student = Student.query.get(id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    data = request.get_json()
    student.name = data.get('name', student.name)
    student.roll_number = data.get('roll_number', student.roll_number)
    student.email = data.get('email', student.email)
    db.session.commit()
    return jsonify({'message': 'Student updated successfully'})

@app.route('/students/<int:id>', methods=['DELETE'])
def delete_student(id):
    student = Student.query.get(id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    db.session.delete(student)
    db.session.commit()
    return jsonify({'message': 'Student deleted successfully'})

# --- Attendance API ---
@app.route('/attendance', methods=['POST'])
def add_attendance():
    data = request.get_json()
    student_id = data.get('student_id')
    date_ = data.get('date')
    status = data.get('status')
    if not student_id or not date_ or not status:
        return jsonify({'error': 'Missing data'}), 400
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    attendance = Attendance(student_id=student_id, date=date_, status=status)
    db.session.add(attendance)
    db.session.commit()
    return jsonify({'message': 'Attendance added successfully', 'id': attendance.id}), 201

@app.route('/attendance', methods=['GET'])
def get_attendance():
    records = Attendance.query.all()
    return jsonify([
        {
            'id': a.id,
            'student_id': a.student_id,
            'student_name': a.student.name,
            'date': a.date,
            'status': a.status
        }
        for a in records
    ])

@app.route('/attendance/<int:id>', methods=['PUT'])
def update_attendance(id):
    attendance = Attendance.query.get(id)
    if not attendance:
        return jsonify({'error': 'Attendance record not found'}), 404
    data = request.get_json()
    attendance.date = data.get('date', attendance.date)
    attendance.status = data.get('status', attendance.status)
    db.session.commit()
    return jsonify({'message': 'Attendance updated successfully'})

@app.route('/attendance/<int:id>', methods=['DELETE'])
def delete_attendance(id):
    attendance = Attendance.query.get(id)
    if not attendance:
        return jsonify({'error': 'Attendance record not found'}), 404
    db.session.delete(attendance)
    db.session.commit()
    return jsonify({'message': 'Attendance deleted successfully'})

# --- Web Frontend CRUD ---
@app.route('/add-student', methods=['GET', 'POST'])
@login_required
def add_student_form():
    message = None
    if request.method == 'POST':
        name = request.form['name']
        roll_number = request.form['roll_number']
        email = request.form['email']
        if Student.query.filter((Student.roll_number == roll_number) | (Student.email == email)).first():
            message = "Student with this roll number or email already exists!"
        else:
            student = Student(name=name, roll_number=roll_number, email=email)
            db.session.add(student)
            db.session.commit()
            message = "Student added successfully!"
    return render_template('add_student.html', message=message)

@app.route('/students-list')
@login_required
def students_list():
    q = request.args.get('q', '').strip()
    students_query = Student.query
    if q:
        students_query = students_query.filter(
            or_(
                Student.name.ilike(f'%{q}%'),
                Student.roll_number.ilike(f'%{q}%'),
                Student.email.ilike(f'%{q}%')
            )
        )

    students = students_query.order_by(Student.id).all()
    settings = Settings.query.first()
    today_dt = date.today()
    student_percentages = {}

    if settings and settings.start_date and settings.end_date:
        # Generate date range from start_date to end_date
        considered_dates = [
            (settings.start_date + timedelta(days=x)).strftime('%Y-%m-%d')
            for x in range((settings.end_date - settings.start_date).days + 1)
        ]
        holiday_dates = set(h.date.strftime("%Y-%m-%d") for h in Holiday.query.all())
        working_days = [d for d in considered_dates if d not in holiday_dates]
        denominator = len(working_days) if working_days else 1
    else:
        working_days = []
        denominator = 1

    for s in students:
        presents = Attendance.query.filter(
            Attendance.student_id == s.id,
            Attendance.status == 'Present',
            Attendance.date.in_(working_days)
        ).count()
        student_percentages[s.id] = round((presents / denominator) * 100, 2) if denominator else 0
        s.ist_time = s.time_added + timedelta(hours=5, minutes=30)

    return render_template(
        'students_list.html',
        students=students,
        student_percentages=student_percentages
    )
@app.route('/edit-student/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    student = Student.query.get_or_404(id)
    message = None
    if request.method == 'POST':
        name = request.form['name']
        roll_number = request.form['roll_number']
        email = request.form['email']
        existing = Student.query.filter(
            ((Student.roll_number == roll_number) | (Student.email == email)) & (Student.id != id)
        ).first()
        if existing:
            message = "Another student with this roll number or email already exists!"
        else:
            student.name = name
            student.roll_number = roll_number
            student.email = email
            db.session.commit()
            message = "Student updated successfully!"
    return render_template('edit_student.html', student=student, message=message)

@app.route('/delete-student/<int:id>')
@login_required
def delete_student_frontend(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    return redirect(url_for('students_list'))

# --- Attendance Settings & Marking + Holiday Management ---
@app.route('/attendance-settings', methods=['GET', 'POST'])
@login_required
def attendance_settings():
    settings = Settings.query.first()
    if not settings:
        settings = Settings()
        db.session.add(settings)
        db.session.commit()

    message = None
    today_str = date.today().strftime("%Y-%m-%d")

    holidays = Holiday.query.all()
    try:
        holiday_dates = {h.date.strftime("%Y-%m-%d") for h in holidays}
    except AttributeError:
        holiday_dates = {str(h.date) for h in holidays}

    is_holiday_today = today_str in holiday_dates

    if request.method == 'POST':
        try:
            if 'add_holiday' in request.form:
                hol_date = request.form.get('holiday_date')
                desc = request.form.get('description')
                if hol_date:
                    date_obj = datetime.strptime(hol_date, '%Y-%m-%d').date()
                    existing_holiday = Holiday.query.filter_by(date=date_obj).first()
                    if not existing_holiday:
                        h = Holiday(date=date_obj, description=desc)
                        db.session.add(h)
                        db.session.commit()
                        message = "Holiday added!"
                    else:
                        message = "Holiday already exists on this date!"

            elif 'remove_holiday' in request.form:
                hol_id = int(request.form.get('remove_holiday'))
                h = Holiday.query.get(hol_id)
                if h:
                    db.session.delete(h)
                    db.session.commit()
                    message = "Holiday removed!"

            elif 'update_settings' in request.form:
                start_date = request.form.get('start_date')
                end_date = request.form.get('end_date')
                if start_date and end_date:
                    settings.start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                    settings.end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                    db.session.commit()
                    message = "Semester dates updated!"

            elif 'mark_attendance' in request.form:
                if not is_holiday_today:
                    for student in Student.query.all():
                        status = request.form.get(f'attendance_{student.id}')
                        if status:
                            existing = Attendance.query.filter_by(
                                student_id=student.id, date=today_str
                            ).first()
                            if existing:
                               
                                    existing.status = status  # update pending
                            else:
                                record = Attendance(
                                    student_id=student.id, date=today_str, status=status
                                )
                                db.session.add(record)
                    db.session.commit()
                    message = "Attendance marked for today!"
                else:
                    message = "Cannot mark attendance—Today is a holiday!"

        except Exception as e:
            db.session.rollback()
            message = f"An error occurred: {str(e)}"

    # Calculate working days and attendance percentages
    students = Student.query.order_by(Student.id).all()

    if settings.start_date and settings.end_date:
        try:
            considered_dates = [
                (settings.start_date + timedelta(days=x)).strftime('%Y-%m-%d')
                for x in range((settings.end_date - settings.start_date).days + 1)
            ]
            working_days = [d for d in considered_dates if d not in holiday_dates]
            denominator = len(working_days) or 1
        except Exception:
            working_days = []
            denominator = 1
    else:
        working_days = []
        denominator = 1

    percentages = {}
    for s in students:
        presents = Attendance.query.filter(
            Attendance.student_id == s.id,
            Attendance.status == 'Present',
            Attendance.date.in_(working_days)
        ).count()
        percentages[s.id] = round((presents / denominator) * 100, 2)

    # ✅ Re-fetch updated today's attendance
    todays_attendance = {
        a.student_id: a.status for a in Attendance.query.filter_by(date=today_str).all()
    }

    return render_template(
        'attendance_settings.html',
        settings=settings,
        students=students,
        percentages=percentages,
        todays_attendance=todays_attendance,
        message=message,
        today=today_str,
        holidays=holidays,
        is_holiday_today=is_holiday_today
    )

# --- Delete attendance for a day (undo feature) ---
@app.route('/delete-attendance/<int:student_id>/<date>', methods=['POST'])
@login_required
def delete_attendance_for_day(student_id, date):
    record = Attendance.query.filter_by(student_id=student_id, date=date).first()
    if record:
        db.session.delete(record)
        db.session.commit()
    return redirect(url_for('attendance_settings'))

# --- Delete attendance record from detailed student page ---
@app.route('/delete-attendance-record/<int:record_id>', methods=['POST'])
@login_required
def delete_attendance_record(record_id):
    record = Attendance.query.get_or_404(record_id)
    student_id = record.student_id
    db.session.delete(record)
    db.session.commit()
    return redirect(url_for('attendance_by_student', student_id=student_id))

# --- Attendance by Student (History) ---
@app.route('/attendance/student/<int:student_id>')
@login_required
def attendance_by_student(student_id):
    student = Student.query.get_or_404(student_id)
    settings = Settings.query.first()

    holidays = {h.date.strftime("%Y-%m-%d") for h in Holiday.query.all()}

    all_records = Attendance.query.filter_by(student_id=student_id).all()
    all_recorded_dates = {rec.date for rec in all_records}

    updated = False
    valid_dates = []

    if settings and settings.start_date and settings.end_date:
        # Build date list from current semester
        all_dates = [
            (settings.start_date + timedelta(days=i)).strftime('%Y-%m-%d')
            for i in range((settings.end_date - settings.start_date).days + 1)
        ]
        valid_dates = [d for d in all_dates if d not in holidays]

        for d in valid_dates:
            if d not in all_recorded_dates:
                new_rec = Attendance(student_id=student_id, date=d, status="Pending")
                db.session.add(new_rec)
                updated = True

    if updated:
        db.session.commit()

    # Filter records again by valid dates only
    records = Attendance.query.filter(
        Attendance.student_id == student_id,
        Attendance.date.in_(valid_dates)
    ).order_by(Attendance.date).all()

    return render_template('attendance_by_student.html', student=student, records=records)

# --- INITIALIZE DB AND ADMIN USER ---


@app.route('/edit-attendance-record/<int:record_id>', methods=['GET', 'POST'])
@login_required
def edit_attendance_record(record_id):
    record = Attendance.query.get_or_404(record_id)
    student_id = record.student_id

    if request.method == 'POST':
        new_status = request.form.get('status')
        if new_status in ['Present', 'Absent', 'Pending']:
            record.status = new_status
            db.session.commit()
            flash('Attendance updated!', 'success')
        return redirect(url_for('attendance_by_student', student_id=student_id))

    return render_template('edit_attendance_record.html', record=record)
if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.mkdir('templates')
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password='admin')
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)
