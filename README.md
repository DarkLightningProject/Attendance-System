 Authentication and User Management
Admin Login:

Secure login and logout functionality using Flask-Login.
Initial admin user automatically created (default credentials: admin/admin).
Authentication is required to access student management, attendance settings, and marking pages.

🎓 Student Management
Add Student:
Add students via a web form (name, roll number, email).
Duplicate check to prevent students with the same email or roll number.
Real-time feedback messages upon successful or failed additions.

View and Search Students:

List all students with details (name, roll number, email, attendance percentage).
Search functionality using names, roll numbers, or emails with a responsive filter.
Edit and Delete Students:
Edit existing student information with validation against duplicates.
Delete students, automatically removing related attendance records (cascade deletion).

📅 Attendance Management
Attendance Recording:

Mark attendance daily for each student as Present, Absent, or Pending.
Attendance marking restricted if the day is marked as a holiday.
Ability to manually update the attendance status afterward.
Attendance Records:
Historical attendance records are generated automatically, marking unrecorded days as "Pending."
Clear status indicators using color-coded badges (Present: green, Absent: yellow, Pending: gray).

Attendance Modification:

Option to edit or delete individual attendance records through intuitive forms.
Ability to delete entire attendance entries for a specific day/student.

🗓️ Semester and Holiday Settings
Semester Date Management:

Admin-defined semester start and end dates to control attendance tracking periods.

Holiday Management:

Add holidays with descriptions to exclude dates from attendance calculations.
Remove holidays through a straightforward interface.
Automatically prevents attendance marking on declared holidays.

📊 Attendance Analytics
Attendance Percentage Calculation:

Automatically calculates attendance percentage based on actual working days (excluding holidays).
Real-time updates reflecting attendance status and historical data.

Individual Attendance Tracking:

Detailed attendance history per student with options for edits and removals.
Comprehensive view of attendance records accessible from the student list.

🌐 API Endpoints (JSON-Based)
Student API:

Create (POST), read (GET), update (PUT), and delete (DELETE) students via JSON APIs.

Attendance API:

Record attendance (POST), retrieve attendance records (GET), update (PUT), and delete (DELETE) through RESTful APIs.

🎨 User Interface & User Experience
Responsive UI:

Modern and responsive design using Bootstrap 5.
Clear and intuitive navigation via navbar and breadcrumb-like navigation.
Feedback Messages:
Informative alerts displayed for actions like addition, deletion, and errors.

🛠️ Technical Stack
Backend: Flask, Flask SQLAlchemy, Flask Login.

Database: SQLite.

Frontend: Jinja2 templates, Bootstrap 5.

Deployment: Development environment configured for easy setup.

🔧 Admin Dashboard (Home Page)
Simple dashboard with quick navigation to add students, view all students, and manage attendance settings.

📁 Data Management
Persistent storage of attendance, students, users, holidays, and settings.
Automatic creation and initialization of necessary database structures upon first run.

