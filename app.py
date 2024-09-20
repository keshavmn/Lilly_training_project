from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Sriramatrust@2015' 
app.config['MYSQL_DB'] = 'attendance' 

def create_connection():
    """ Create a database connection to the MySQL database. """
    connection = None
    try:
        connection = mysql.connector.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD']
        )
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

def create_database():
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {app.config['MYSQL_DB']}")
    cursor.close()
    connection.close()

def create_tables():
    connection = create_connection()
    connection.database = app.config['MYSQL_DB']  # Select the database
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INT AUTO_INCREMENT PRIMARY KEY,
            date VARCHAR(50) NOT NULL,
            status VARCHAR(10) NOT NULL,
            student_id INT,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        )
    """)
    connection.commit()
    cursor.close()
    connection.close()

# Create database and tables if they don't exist
create_database()
create_tables()

# Routes
@app.route('/')
def index():
    return redirect(url_for('students_list'))

@app.route('/students')
def students_list():
    connection = create_connection()
    connection.database = app.config['MYSQL_DB']  # Select the database
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('students.html', students=students)

@app.route('/students/add', methods=['POST'])
def add_student():
    name = request.form.get('name')
    connection = create_connection()
    connection.database = app.config['MYSQL_DB']  # Select the database
    cursor = connection.cursor()
    cursor.execute("INSERT INTO students (name) VALUES (%s)", (name,))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect(url_for('students_list'))

@app.route('/students/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    connection = create_connection()
    connection.database = app.config['MYSQL_DB']  # Select the database
    cursor = connection.cursor(dictionary=True)
    
    if request.method == 'POST':
        name = request.form.get('name')
        cursor.execute("UPDATE students SET name = %s WHERE id = %s", (name, id))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('students_list'))
    
    cursor.execute("SELECT * FROM students WHERE id = %s", (id,))
    student = cursor.fetchone()
    cursor.close()
    connection.close()
    return render_template('edit_student.html', student=student)

@app.route('/students/delete/<int:id>')
def delete_student(id):
    connection = create_connection()
    connection.database = app.config['MYSQL_DB']  # Select the database
    cursor = connection.cursor()
    
    # The foreign key constraint will handle the deletion of attendance records
    cursor.execute("DELETE FROM students WHERE id = %s", (id,))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect(url_for('students_list'))

@app.route('/attendance')
def attendance_list():
    connection = create_connection()
    connection.database = app.config['MYSQL_DB']  # Select the database
    cursor = connection.cursor(dictionary=True)
    
    # Fetch attendance records along with student names
    cursor.execute("""
        SELECT a.*, s.name AS student_name 
        FROM attendance a 
        LEFT JOIN students s ON a.student_id = s.id
    """)
    attendance_records = cursor.fetchall()
    
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    error = request.args.get('error')  # Get the error message if any
    return render_template('attendance.html', attendance=attendance_records, students=students, error=error)

@app.route('/attendance/add', methods=['POST'])
def add_attendance():
    date = request.form.get('date')
    status = request.form.get('status')
    student_id = request.form.get('student_id')
    
    if not date or not status or not student_id:
        return redirect(url_for('attendance_list'))

    connection = create_connection()
    connection.database = app.config['MYSQL_DB']  # Select the database
    cursor = connection.cursor()
    
    # Check if attendance record already exists for this student on the given date
    cursor.execute("""
        SELECT * FROM attendance 
        WHERE student_id = %s AND date = %s
    """, (student_id, date))
    
    existing_record = cursor.fetchone()
    
    if existing_record:
        cursor.close()
        connection.close()
        return redirect(url_for('attendance_list', error='Attendance already recorded for this student on this date.'))

    # Insert new attendance record if no duplicates found
    cursor.execute("INSERT INTO attendance (date, status, student_id) VALUES (%s, %s, %s)", (date, status, student_id))
    connection.commit()
    cursor.close()
    connection.close()
    
    return redirect(url_for('attendance_list'))

@app.route('/attendance/edit/<int:id>', methods=['GET', 'POST'])
def edit_attendance(id):
    connection = create_connection()
    connection.database = app.config['MYSQL_DB']  # Select the database
    cursor = connection.cursor(dictionary=True)
    
    if request.method == 'POST':
        date = request.form.get('date')
        status = request.form.get('status')
        student_id = request.form.get('student_id')
        cursor.execute("UPDATE attendance SET date = %s, status = %s, student_id = %s WHERE id = %s", (date, status, student_id, id))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('attendance_list'))
    
    cursor.execute("SELECT * FROM attendance WHERE id = %s", (id,))
    attendance = cursor.fetchone()
    
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template('edit_attendance.html', attendance=attendance, students=students)

@app.route('/attendance/delete/<int:id>')
def delete_attendance(id):
    connection = create_connection()
    connection.database = app.config['MYSQL_DB']  # Select the database
    cursor = connection.cursor()
    cursor.execute("DELETE FROM attendance WHERE id = %s", (id,))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect(url_for('attendance_list'))

if __name__ == '__main__':
    app.run(debug=True, port='5002')
