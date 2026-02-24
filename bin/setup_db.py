import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Role, User, College, Course, Semester, Subject, Unit, Topic, StudentRegistry
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Only create tables if they don't exist.
    db.create_all()
    
    # 1. Seed Roles
    roles = ['Admin', 'Faculty', 'Student']
    for role_name in roles:
        if not Role.query.filter_by(name=role_name).first():
            role = Role(name=role_name)
            db.session.add(role)
    db.session.commit()
    print("Roles seeded (Admin, Faculty, Student).")

    # 2. Seed Single College: Nilgiri College
    college = College.query.filter_by(name='Nilgiri College').first()
    if not college:
        existing_college = College.query.first()
        if existing_college:
            existing_college.name = 'Nilgiri College'
            college = existing_college
        else:
            college = College(name='Nilgiri College')
            db.session.add(college)
        db.session.commit()
    
    # 3. CRITICAL: Clear existing data to ensure strictly requested counts
    print("Clearing existing data for a clean Nilgiri setup...")
    StudentRegistry.query.delete()
    User.query.filter(User.email != 'admin@ncas.edu').delete()
    # Explicitly clear syllabus hierarchy to ensure no orphans/duplicates
    Topic.query.delete()
    Unit.query.delete()
    Subject.query.delete()
    Semester.query.delete()
    Course.query.delete() 
    db.session.commit()

    # 4. Seed Courses and Diversified Subjects (6 Semesters each)
    course_data = {
        'B.Sc Computer Science': {
            1: ['Python Programming', 'Discrete Mathematics'],
            2: ['Data Structures', 'Operating Systems'],
            3: ['Database Management', 'Computer Networks'],
            4: ['Software Engineering', 'Java Programming'],
            5: ['Artificial Intelligence', 'Web Technologies'],
            6: ['Network Security', 'Cloud Computing']
        },
        'B.A. English': {
            1: ['English Literature', 'Phonetics'],
            2: ['Modern Poetry', 'Indian Writing in English'],
            3: ['American Literature', 'Shakespearean Drama'],
            4: ['Colonial Discourse', 'Literary Criticism'],
            5: ['Modernism & Post-modernism', 'Comparative Literature'],
            6: ['Creative Writing', 'Media Studies']
        },
        'B.Com Finance': {
            1: ['Financial Accounting', 'Business Statistics'],
            2: ['Corporate Finance', 'Cost Accounting'],
            3: ['Advanced Management Accounting', 'Taxation Law'],
            4: ['Investment Management', 'Auditing'],
            5: ['International Finance', 'Financial Markets'],
            6: ['Wealth Management', 'Corporate Law']
        },
        'BBA Logistics': {
            1: ['Supply Chain Management', 'Principles of Management'],
            2: ['Inventory Control', 'Warehouse Management'],
            3: ['Logistics Management', 'Shipping & Documentation'],
            4: ['Procurement & Sourcing', 'Transportation Systems'],
            5: ['Retail Logistics', 'Export & Import Trade'],
            6: ['E-commerce Logistics', 'Strategic SCM']
        },
        'B.Sc Psychology': {
            1: ['General Psychology', 'Developmental Psychology'],
            2: ['Social Psychology', 'Research Methodology'],
            3: ['Cognitive Psychology', 'Biological Basis of Behavior'],
            4: ['Abnormal Psychology', 'Health Psychology'],
            5: ['Counselling Psychology', 'Industrial Psychology'],
            6: ['Clinical Psychology', 'Positive Psychology']
        },
        'Bachelor of Computer Applications': {
            1: ['C Programming', 'Mathematical Foundations'],
            2: ['Object Oriented Programming', 'System Architecture'],
            3: ['Data Communication', 'Analysis of Algorithms'],
            4: ['Mobile Application Development', 'Unix Shell Programming'],
            5: ['Information Security', 'Visual Programming'],
            6: ['Digital Marketing', 'Soft Computing']
        }
    }

    created_courses = []
    for c_name, semester_data in course_data.items():
        course = Course(name=c_name, college_id=college.id)
        db.session.add(course)
        db.session.flush() # Get ID
        
        for sem_num, subjects in semester_data.items():
            semester = Semester(number=sem_num, course_id=course.id)
            db.session.add(semester)
            db.session.flush()
            
            for s_name in subjects:
                subject = Subject(name=s_name, semester_id=semester.id)
                db.session.add(subject)
                db.session.flush()
                
                # Add a dummy unit and topic for each subject to prevent empty states
                unit = Unit(number=1, subject_id=subject.id)
                db.session.add(unit)
                db.session.flush()
                
                topic = Topic(name=f"Introduction to {s_name}", unit_id=unit.id)
                db.session.add(topic)
        
        created_courses.append(course)
    
    db.session.commit()
    print(f"Seeded {len(created_courses)} courses with 6 semesters and unique subjects each.")

    # 5. Create Initial Admin: admin@ncas.edu / admin123
    admin_email = 'admin@ncas.edu'
    admin_user = User.query.filter_by(role=Role.query.filter_by(name='Admin').first()).first()
    if admin_user:
        admin_user.email = admin_email
        admin_user.username = admin_email
        admin_user.password_hash = generate_password_hash('admin123')
    else:
        admin_role = Role.query.filter_by(name='Admin').first()
        admin_user = User(
            username=admin_email,
            email=admin_email,
            password_hash=generate_password_hash('admin123'),
            role=admin_role,
            college_id=college.id,
            is_verified=True
        )
        db.session.add(admin_user)
    db.session.commit()
    print(f"Admin initialized: {admin_email} / admin123")

    # 6. Seed 10 Faculties
    faculty_role = Role.query.filter_by(name='Faculty').first()
    for i in range(1, 11):
        email = f'faculty{i}@ncas.edu'
        if not User.query.filter_by(email=email).first():
            user = User(
                username=f'faculty{i}',
                email=email,
                name=f'Faculty Member {i}',
                password_hash=generate_password_hash('password123'),
                role=faculty_role,
                college_id=college.id,
                is_verified=True
            )
            db.session.add(user)
    db.session.commit()
    print("10 Faculty accounts seeded.")

    # 7. Seed 20 Students
    student_role = Role.query.filter_by(name='Student').first()
    for i in range(1, 21):
        email = f'stud{i}@ncas.edu'
        reg_num = f'REG{1000+i}'
        
        if not StudentRegistry.query.filter_by(email=email).first():
            registry = StudentRegistry(
                email=email,
                register_number=reg_num,
                college_id=college.id,
                is_registered=True
            )
            db.session.add(registry)
            
        if not User.query.filter_by(email=email).first():
            user = User(
                username=f'stud{i}',
                email=email,
                name=f'Student {i}',
                password_hash=generate_password_hash('password123'),
                role=student_role,
                college_id=college.id,
                register_number=reg_num,
                is_verified=True
            )
            db.session.add(user)
    db.session.commit()
    print("20 Student accounts seeded.")

    print("Database customized for Nilgiri College with full curriculum successfully.")
