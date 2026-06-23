"""
Database Setup and Utilities
Creates all tables and sample data for the FAU Smart Academic Assistant
"""
import sqlite3
import os
import json
from datetime import datetime, date

# Database path
DB_DIR = os.path.join(os.path.dirname(__file__), "database")
DB_PATH = os.path.join(DB_DIR, "fau_streamlit.db")


def init_database():
    """Initialize complete database with all tables and sample data"""
    
    # Create database directory
    os.makedirs(DB_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("🔧 Creating database tables...")
    
    # 1. STUDENTS TABLE (Enhanced)
    c.execute('''
        CREATE TABLE IF NOT EXISTS students(
            znumber TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            major TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            catalog_year TEXT DEFAULT '2021',
            gpa REAL DEFAULT 3.5,
            total_credits INTEGER DEFAULT 90,
            advisor_name TEXT DEFAULT 'Academic Advisor',
            advisor_email TEXT DEFAULT 'advisor@fau.edu',
            classification TEXT DEFAULT 'Junior',
            date_of_birth TEXT,
            phone TEXT,
            address TEXT
        )
    ''')
    
    # 2. TRANSCRIPTS TABLE (Student course history)
    c.execute('''
        CREATE TABLE IF NOT EXISTS transcripts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            znumber TEXT NOT NULL,
            course_code TEXT NOT NULL,
            course_title TEXT NOT NULL,
            credits INTEGER DEFAULT 3,
            grade TEXT,
            semester TEXT,
            year INTEGER,
            FOREIGN KEY (znumber) REFERENCES students(znumber)
        )
    ''')
    
    # 3. COURSES TABLE (Course catalog)
    c.execute('''
        CREATE TABLE IF NOT EXISTS courses(
            course_code TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            credits INTEGER DEFAULT 3,
            prerequisites TEXT,
            description TEXT,
            department TEXT,
            instructor TEXT
        )
    ''')
    
    # 4. MAJOR REQUIREMENTS TABLE
    c.execute('''
        CREATE TABLE IF NOT EXISTS major_requirements(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            major_name TEXT NOT NULL,
            min_gpa REAL DEFAULT 2.0,
            min_credits INTEGER DEFAULT 30,
            required_courses TEXT,
            total_credits_required INTEGER DEFAULT 120
        )
    ''')
    
    # 5. SUBMISSIONS TABLE (Form submissions)
    c.execute('''
        CREATE TABLE IF NOT EXISTS submissions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            znumber TEXT NOT NULL,
            form_name TEXT NOT NULL,
            payload TEXT,
            file_name TEXT,
            date TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            auto_filled INTEGER DEFAULT 0,
            confidence_score REAL DEFAULT 0.0,
            FOREIGN KEY (znumber) REFERENCES students(znumber)
        )
    ''')
    
    # 6. REMINDERS TABLE
    c.execute('''
        CREATE TABLE IF NOT EXISTS reminders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            znumber TEXT NOT NULL,
            message TEXT NOT NULL,
            due_date TEXT NOT NULL,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY (znumber) REFERENCES students(znumber)
        )
    ''')
    
    # 7. ADMIN TABLE
    c.execute('''
        CREATE TABLE IF NOT EXISTS admin(
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    ''')
    
    # 8. FORM DEADLINES TABLE
    c.execute('''
        CREATE TABLE IF NOT EXISTS form_deadlines(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            form_name TEXT NOT NULL,
            semester TEXT NOT NULL,
            deadline_date TEXT NOT NULL,
            description TEXT
        )
    ''')
    
    conn.commit()
    print("✅ Database tables created!")
    
    # Insert sample data
    insert_sample_data(conn)
    
    conn.close()
    print("✅ Database initialization complete!")
    print(f"📁 Database location: {DB_PATH}")


def insert_sample_data(conn):
    """Insert sample data for testing"""
    c = conn.cursor()
    
    # Check if data already exists
    c.execute("SELECT COUNT(*) FROM students")
    if c.fetchone()[0] > 0:
        print("ℹ️  Sample data already exists, skipping...")
        return
    
    print("📝 Inserting sample data...")
    
    # SAMPLE STUDENTS
    students = [
        ("Z1000001", "John", "Doe", "Computer Science", "john.doe@fau.edu", "password123",
         "2021", 3.5, 95, "Dr. Sarah Smith", "s.smith@fau.edu", "Senior", "2002-05-15", "561-555-0001", "123 Campus Dr, Boca Raton, FL"),
        
        ("Z1000002", "Emily", "Stone", "Mechanical Engineering", "emily.stone@fau.edu", "password123",
         "2022", 3.2, 75, "Dr. Michael Johnson", "m.johnson@fau.edu", "Junior", "2003-08-22", "561-555-0002", "456 College Ave, Boca Raton, FL"),
        
        ("Z1000003", "Michael", "Chen", "Computer Engineering", "michael.chen@fau.edu", "password123",
         "2021", 3.8, 110, "Dr. Jennifer Williams", "j.williams@fau.edu", "Senior", "2001-12-10", "561-555-0003", "789 University Blvd, Boca Raton, FL"),
        
        ("Z1000004", "Sarah", "Martinez", "Computer Science", "sarah.martinez@fau.edu", "password123",
         "2023", 2.9, 45, "Dr. Sarah Smith", "s.smith@fau.edu", "Sophomore", "2004-03-18", "561-555-0004", "321 Student Ln, Boca Raton, FL"),
        
        ("Z1000005", "David", "Brown", "Business Administration", "david.brown@fau.edu", "password123",
         "2022", 3.6, 88, "Dr. Robert Davis", "r.davis@fau.edu", "Junior", "2003-11-05", "561-555-0005", "654 Academic Way, Boca Raton, FL"),
    ]
    
    c.executemany("""
        INSERT INTO students VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, students)
    print(f"  ✓ Inserted {len(students)} students")
    
    # SAMPLE TRANSCRIPTS
    transcripts = [
        # John Doe (Z1000001) - Senior, almost ready to graduate
        ("Z1000001", "COP 2210", "Computer Programming I", 3, "A", "Fall", 2021),
        ("Z1000001", "COP 3330", "Object Oriented Programming", 3, "A", "Spring", 2022),
        ("Z1000001", "COP 4331", "Processes for OOP Software", 3, "A-", "Fall", 2022),
        ("Z1000001", "MAD 3512", "Theory of Algorithms", 3, "B+", "Spring", 2023),
        ("Z1000001", "COT 3100", "Discrete Mathematics", 3, "A", "Fall", 2023),
        ("Z1000001", "COP 4520", "Parallel Systems", 3, "B+", "Spring", 2024),
        ("Z1000001", "CAP 4630", "Artificial Intelligence", 3, "A", "Fall", 2024),
        ("Z1000001", "COP 4710", "Database Systems", 3, "A-", "Fall", 2024),
        
        # Emily Stone (Z1000002) - Junior, Mechanical Engineering
        ("Z1000002", "EGN 1007", "Engineering Concepts", 1, "A", "Fall", 2022),
        ("Z1000002", "EGN 3310", "Engineering Analysis", 3, "B", "Spring", 2023),
        ("Z1000002", "EML 3222", "Thermodynamics", 3, "B+", "Fall", 2023),
        ("Z1000002", "EML 3034", "Modeling Methods", 3, "B", "Spring", 2024),
        ("Z1000002", "EML 4140", "Thermal Systems Design", 3, "B+", "Fall", 2024),
        
        # Michael Chen (Z1000003) - Senior, ready to graduate
        ("Z1000003", "COP 2210", "Computer Programming I", 3, "A", "Fall", 2021),
        ("Z1000003", "COP 3330", "Object Oriented Programming", 3, "A", "Spring", 2022),
        ("Z1000003", "EEL 3801", "Computer Organization", 3, "A", "Fall", 2022),
        ("Z1000003", "EEL 4746", "Microprocessor Systems", 3, "A-", "Spring", 2023),
        ("Z1000003", "COP 4331", "Processes for OOP Software", 3, "A", "Fall", 2023),
        ("Z1000003", "EEL 4851", "Embedded Systems", 3, "A", "Spring", 2024),
        
        # Sarah Martinez (Z1000004) - Sophomore, struggling GPA
        ("Z1000004", "COP 2210", "Computer Programming I", 3, "C+", "Fall", 2023),
        ("Z1000004", "MAC 2311", "Calculus I", 4, "C", "Fall", 2023),
        ("Z1000004", "COP 3330", "Object Oriented Programming", 3, "B-", "Spring", 2024),
        ("Z1000004", "COT 3100", "Discrete Mathematics", 3, "C+", "Spring", 2024),
        ("Z1000004", "MAC 2312", "Calculus II", 4, "C-", "Fall", 2024),
    ]
    
    c.executemany("""
        INSERT INTO transcripts (znumber, course_code, course_title, credits, grade, semester, year)
        VALUES (?,?,?,?,?,?,?)
    """, transcripts)
    print(f"  ✓ Inserted {len(transcripts)} transcript records")
    
    # SAMPLE COURSES
    courses = [
        ("COP 2210", "Computer Programming I", 3, "None", "Introduction to programming", "Computer Science", "Dr. Anderson"),
        ("COP 3330", "Object Oriented Programming", 3, "COP 2210", "OOP concepts and design", "Computer Science", "Dr. Brown"),
        ("COP 4331", "Processes for OOP Software", 3, "COP 3330", "Software engineering project", "Computer Science", "Dr. Smith"),
        ("COP 4520", "Parallel and Distributed Systems", 3, "COP 3330", "Advanced systems programming", "Computer Science", "Dr. Wilson"),
        ("MAD 3512", "Theory of Algorithms", 3, "COT 3100", "Algorithm design and analysis", "Computer Science", "Dr. Taylor"),
        ("COT 3100", "Discrete Mathematics", 3, "MAC 2311", "Mathematical foundations", "Computer Science", "Dr. Johnson"),
        ("CAP 4630", "Artificial Intelligence", 3, "COP 3330,COT 3100", "AI concepts and applications", "Computer Science", "Dr. Davis"),
        ("COP 4710", "Database Systems", 3, "COP 3330", "Database design and SQL", "Computer Science", "Dr. Martinez"),
        ("EGN 3310", "Engineering Analysis", 3, "MAC 2312", "Engineering problem solving", "Engineering", "Dr. Chen"),
        ("EML 3222", "Thermodynamics", 3, "PHY 2049", "Heat and energy systems", "Mechanical Engineering", "Dr. Lopez"),
        ("EEL 3801", "Computer Organization", 3, "COP 2210", "Hardware and assembly", "Computer Engineering", "Dr. Garcia"),
    ]
    
    c.executemany("""
        INSERT INTO courses VALUES (?,?,?,?,?,?,?)
    """, courses)
    print(f"  ✓ Inserted {len(courses)} courses")
    
    # MAJOR REQUIREMENTS
    majors = [
        ("Computer Science", 2.5, 30, "COP 2210,COP 3330,COP 4331,MAD 3512,COT 3100", 120),
        ("Mechanical Engineering", 2.5, 30, "EGN 3310,EML 3222,EML 4140", 128),
        ("Computer Engineering", 2.5, 30, "COP 3330,EEL 3801,EEL 4746", 126),
        ("Business Administration", 2.0, 24, "ACG 2021,ECO 2013,FIN 3403", 120),
    ]
    
    c.executemany("""
        INSERT INTO major_requirements VALUES (NULL,?,?,?,?,?)
    """, majors)
    print(f"  ✓ Inserted {len(majors)} major requirements")
    
    # ADMIN USER
    c.execute("INSERT INTO admin VALUES (?,?)", ("admin", "admin123"))
    print("  ✓ Created admin user (username: admin, password: admin123)")
    
    # FORM DEADLINES
    deadlines = [
        ("Graduation Application", "Fall 2025", "2025-10-01", "Graduation application deadline for Fall 2025"),
        ("Graduation Application", "Spring 2026", "2026-03-01", "Graduation application deadline for Spring 2026"),
        ("Graduation Application", "Summer 2025", "2025-07-01", "Graduation application deadline for Summer 2025"),
        ("Change of Major", "Spring 2026", "2025-12-15", "Last day to change major for Spring 2026"),
        ("Change of Major", "Fall 2025", "2025-08-15", "Last day to change major for Fall 2025"),
        ("Course Override", "Spring 2026", "2026-01-15", "Course override requests for Spring 2026"),
    ]
    
    c.executemany("""
        INSERT INTO form_deadlines VALUES (NULL,?,?,?,?)
    """, deadlines)
    print(f"  ✓ Inserted {len(deadlines)} form deadlines")
    
    conn.commit()
    print("✅ Sample data inserted successfully!")


# Utility functions for database operations

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)


def get_student(znumber):
    """Get student information"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT znumber, first_name, last_name, major, email, catalog_year,
               gpa, total_credits, advisor_name, advisor_email, classification
        FROM students WHERE znumber=?
    """, (znumber,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return {
            "znumber": row[0],
            "first_name": row[1],
            "last_name": row[2],
            "major": row[3],
            "email": row[4],
            "catalog_year": row[5],
            "gpa": row[6],
            "total_credits": row[7],
            "advisor_name": row[8],
            "advisor_email": row[9],
            "classification": row[10]
        }
    return None


def check_student_login(znumber, password):
    """Verify student login credentials"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT password FROM students WHERE znumber=?", (znumber,))
    row = c.fetchone()
    conn.close()
    return row is not None and row[0] == password


def check_admin_login(username, password):
    """Verify admin login credentials"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT password FROM admin WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return row is not None and row[0] == password


def get_student_transcript(znumber):
    """Get student's complete transcript"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT course_code, course_title, credits, grade, semester, year
        FROM transcripts
        WHERE znumber=?
        ORDER BY year DESC, semester
    """, (znumber,))
    rows = c.fetchall()
    conn.close()
    
    return [
        {
            "course_code": row[0],
            "course_title": row[1],
            "credits": row[2],
            "grade": row[3],
            "semester": row[4],
            "year": row[5]
        }
        for row in rows
    ]


def calculate_gpa(transcript):
    """Calculate GPA from transcript"""
    grade_points = {
        "A": 4.0, "A-": 3.7,
        "B+": 3.3, "B": 3.0, "B-": 2.7,
        "C+": 2.3, "C": 2.0, "C-": 1.7,
        "D+": 1.3, "D": 1.0, "D-": 0.7,
        "F": 0.0
    }
    
    total_points = 0
    total_credits = 0
    
    for course in transcript:
        grade = course["grade"]
        credits = course["credits"]
        if grade in grade_points:
            total_points += grade_points[grade] * credits
            total_credits += credits
    
    return round(total_points / total_credits, 2) if total_credits > 0 else 0.0


def get_course_info(course_code):
    """Get course information from catalog"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT title, credits, prerequisites, description, department, instructor
        FROM courses WHERE course_code=?
    """, (course_code,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return {
            "title": row[0],
            "credits": row[1],
            "prerequisites": row[2],
            "description": row[3],
            "department": row[4],
            "instructor": row[5]
        }
    return None


def save_submission(znumber, form_name, payload, file_name=None, auto_filled=False, confidence_score=0.0):
    """Save form submission"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO submissions 
        (znumber, form_name, payload, file_name, date, status, auto_filled, confidence_score)
        VALUES (?,?,?,?,?,?,?,?)
    """, (znumber, form_name, json.dumps(payload), file_name, 
          date.today().isoformat(), 'pending', 1 if auto_filled else 0, confidence_score))
    conn.commit()
    conn.close()


# Run this script directly to initialize database
if __name__ == "__main__":
    print("=" * 60)
    print("FAU SMART ACADEMIC ASSISTANT - DATABASE INITIALIZATION")
    print("=" * 60)
    init_database()
    print("\n✨ Database ready for use!")
    print("\n📚 Sample student accounts created:")
    print("   Z1000001 / password123 (John - Senior CS, ready to graduate)")
    print("   Z1000002 / password123 (Emily - Junior ME)")
    print("   Z1000003 / password123 (Michael - Senior CE, ready to graduate)")
    print("   Z1000004 / password123 (Sarah - Sophomore CS, low GPA)")
    print("   Z1000005 / password123 (David - Junior Business)")
    print("\n👤 Admin account:")
    print("   admin / admin123")
    print("=" * 60)