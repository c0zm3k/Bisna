from flask import render_template, url_for, flash, redirect, request, Blueprint, make_response
from flask_login import login_required, current_user
from app import db
from app.models import Course, Semester, Subject, Unit, Topic, Role, StudentRegistry, User, College
from app.forms import CourseForm, SemesterForm, SubjectForm, UnitForm, TopicForm, CSVUploadForm
from app.decorators import admin_required, role_required
from app.utils import log_activity
import pandas as pd
from werkzeug.utils import secure_filename
import os

admin = Blueprint('admin', __name__)

@admin.route('/admin/dashboard')
@login_required
@admin_required
def dashboard():
    courses = Course.query.all()
    
    # Fetch pending facultys for THIS college
    pending_facultys = User.query.join(Role).filter(
        User.is_verified == False,
        Role.name == 'Faculty'
    ).all()

    verified_facultys = User.query.join(Role).filter(
        User.is_verified == True,
        Role.name == 'Faculty'
    ).all()

    # Fetch verified students
    verified_students = User.query.join(Role).filter(
        User.is_verified == True,
        Role.name == 'Student'
    ).all()
    
    return render_template('admin/dashboard.html', 
                           courses=courses, 
                           pending_facultys=pending_facultys,
                           verified_facultys=verified_facultys,
                           verified_students=verified_students)

@admin.route('/admin/faculty')
@login_required
@role_required('Admin')
def view_faculty():
    verified_facultys = User.query.join(Role).filter(
        User.is_verified == True,
        Role.name == 'Faculty'
    ).all()
    return render_template('admin/faculty.html', verified_facultys=verified_facultys)

@admin.route('/admin/students')
@login_required
@role_required('Admin', 'Faculty')
def view_students():
    verified_students = User.query.join(Role).filter(
        User.is_verified == True,
        Role.name == 'Student'
    ).all()
    
    # Contextual title/back link for Admin vs Faculty
    return render_template('admin/students.html', verified_students=verified_students)

@admin.route('/admin/verify_faculty/<int:user_id>/<action>')
@login_required
@role_required('Admin')
def verify_faculty(user_id, action):
    user = User.query.get_or_404(user_id)
    
    # Security check: Single college setup - all belong to same college
    pass
        
    if action == 'approve':
        user.is_verified = True
        log_activity('Verify Faculty', f'Approved faculty {user.username}')
        flash(f'Faculty {user.username} approved.', 'success')
    elif action == 'reject':
        username = user.username
        log_activity('Verify Faculty', f'Rejected faculty {username}')
        db.session.delete(user)
        flash(f'Faculty {username} rejected.', 'danger')
    
    db.session.commit()
    return redirect(url_for('admin.dashboard'))

@admin.route('/admin/delete_faculty/<int:user_id>', methods=['POST'])
@login_required
@role_required('Admin')
def delete_faculty(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.role.name != 'Faculty':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    username = user.username
    log_activity('Delete Faculty', f'Deleted faculty {username}')
    db.session.delete(user)
    db.session.commit()
    flash(f'Faculty {username} deleted.', 'success')
    return redirect(url_for('admin.dashboard'))

@admin.route('/admin/logs')
@login_required
@role_required('Admin')
def view_logs():
    # Filter logs for 'Faculty' role users in THIS college
    from app.models import ActivityLog
    logs = ActivityLog.query.join(User).join(Role).filter(
        Role.name == 'Faculty'
    ).order_by(ActivityLog.timestamp.desc()).all()
    return render_template('admin/logs.html', logs=logs, title='Faculty Activity Logs')

@admin.route('/admin/manage/course', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Faculty')
def manage_course():
    form = CourseForm()
    if form.validate_on_submit():
        primary_college = College.query.first()
        course = Course(name=form.name.data, college_id=primary_college.id)
        db.session.add(course)
        db.session.commit()
        log_activity('Add Course', f'Added course {course.name}')
        flash('Course Added!', 'success')
        if request.args.get('next'):
            return redirect(request.args.get('next'))
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/manage_syllabus.html', form=form, title='Add Course')

@admin.route('/admin/manage/semester', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Faculty')
def manage_semester():
    form = SemesterForm()
    form.course.choices = [(c.id, c.name) for c in Course.query.all()]
    if request.method == 'GET' and request.args.get('course'):
        form.course.data = int(request.args.get('course'))
    
    if form.validate_on_submit():
        semester = Semester(number=form.number.data, course_id=form.course.data)
        db.session.add(semester)
        db.session.commit()
        log_activity('Add Semester', f'Added Semester {semester.number} for course {semester.course.name}')
        flash('Semester Added!', 'success')
        if request.args.get('next'):
            return redirect(request.args.get('next'))
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/manage_syllabus.html', form=form, title='Add Semester')

@admin.route('/admin/manage/subject', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Faculty')
def manage_subject():
    form = SubjectForm()
    # Chain selection: only semesters belonging to courses in this college
    form.semester.choices = [(s.id, f"{s.course.name} - Semester {s.number}") for s in Semester.query.all()]
    if request.method == 'GET' and request.args.get('semester'):
        form.semester.data = int(request.args.get('semester'))

    if form.validate_on_submit():
        subject = Subject(name=form.name.data, semester_id=form.semester.data)
        db.session.add(subject)
        db.session.commit()
        log_activity('Add Subject', f'Added Subject {subject.name} to Semester {subject.semester.number}')
        flash('Subject Added!', 'success')
        if request.args.get('next'):
            return redirect(request.args.get('next'))
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/manage_syllabus.html', form=form, title='Add Subject')

# --- Edit/Delete Routes ---

@admin.route('/admin/edit/course/<int:course_id>', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Faculty')
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    form = CourseForm(obj=course)
    if form.validate_on_submit():
        course.name = form.name.data
        db.session.commit()
        log_activity('Edit Course', f'Updated course name to {course.name}')
        flash('Course Updated!', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/manage_syllabus.html', form=form, title='Edit Course', is_edit=True)

@admin.route('/admin/delete/course/<int:course_id>', methods=['POST'])
@login_required
@role_required('Admin', 'Faculty')
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    course_name = course.name
    db.session.delete(course)
    db.session.commit()
    log_activity('Delete Course', f'Deleted course {course_name}')
    flash(f'Course "{course_name}" Deleted!', 'success')
    return redirect(url_for('admin.dashboard'))

@admin.route('/admin/edit/semester/<int:sem_id>', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Faculty')
def edit_semester(sem_id):
    sem = Semester.query.get_or_404(sem_id)
    # Security check: Single college setup - all belong to same college
    pass
    form = SemesterForm(obj=sem)
    form.course.choices = [(c.id, c.name) for c in Course.query.all()]
    if form.validate_on_submit():
        sem.number = form.number.data
        sem.course_id = form.course.data
        db.session.commit()
        log_activity('Edit Semester', f'Updated Semester {sem.number} for course {sem.course.name}')
        flash('Semester Updated!', 'success')
        return redirect(url_for('admin.dashboard'))
    form.course.data = sem.course_id
    return render_template('admin/manage_syllabus.html', form=form, title='Edit Semester', is_edit=True)

@admin.route('/admin/delete/semester/<int:sem_id>', methods=['POST'])
@login_required
@role_required('Admin', 'Faculty')
def delete_semester(sem_id):
    sem = Semester.query.get_or_404(sem_id)
    sem_num = sem.number
    course_name = sem.course.name
    db.session.delete(sem)
    db.session.commit()
    log_activity('Delete Semester', f'Deleted Semester {sem_num} for course {course_name}')
    flash(f'Semester {sem_num} Deleted!', 'success')
    return redirect(url_for('admin.dashboard'))

@admin.route('/admin/edit/subject/<int:sub_id>', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Faculty')
def edit_subject(sub_id):
    sub = Subject.query.get_or_404(sub_id)
    # Security check: Single college setup 
    pass
    form = SubjectForm(obj=sub)
    form.semester.choices = [(s.id, f"{s.course.name} - Semester {s.number}") for s in Semester.query.all()]
    if form.validate_on_submit():
        sub.name = form.name.data
        sub.semester_id = form.semester.data
        db.session.commit()
        log_activity('Edit Subject', f'Updated Subject {sub.name}')
        flash('Subject Updated!', 'success')
        return redirect(url_for('admin.dashboard'))
    form.semester.data = sub.semester_id
    return render_template('admin/manage_syllabus.html', form=form, title='Edit Subject', is_edit=True)

@admin.route('/admin/delete/subject/<int:sub_id>', methods=['POST'])
@login_required
@role_required('Admin', 'Faculty')
def delete_subject(sub_id):
    sub = Subject.query.get_or_404(sub_id)
    sub_name = sub.name
    db.session.delete(sub)
    db.session.commit()
    log_activity('Delete Subject', f'Deleted Subject {sub_name}')
    flash(f'Subject "{sub_name}" Deleted!', 'success')
    return redirect(url_for('admin.dashboard'))

@admin.route('/admin/manage/unit', methods=['GET', 'POST'])
@login_required
@role_required('Faculty')
def manage_unit():
    form = UnitForm()
    form.subject.choices = [(s.id, s.name) for s in Subject.query.all()]
    if form.validate_on_submit():
        unit = Unit(number=form.number.data, subject_id=form.subject.data)
        db.session.add(unit)
        db.session.commit()
        log_activity('Add Unit', f'Added Unit {unit.number} to {unit.subject.name}')
        flash('Unit Added!', 'success')
        if request.args.get('next'):
            return redirect(request.args.get('next'))
        
        # Determine redirect based on role (though strictly restricted to Faculty now)
        if current_user.role.name == 'Faculty':
             return redirect(url_for('main.faculty_dashboard'))
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/manage_syllabus.html', form=form, title='Add Unit')

@admin.route('/admin/manage/topic', methods=['GET', 'POST'])
@login_required
@role_required('Faculty')
def manage_topic():
    form = TopicForm()
    form.unit.choices = [(u.id, f"{u.subject.name} - Unit {u.number}") for u in Unit.query.all()]
    if form.validate_on_submit():
        topic = Topic(name=form.name.data, unit_id=form.unit.data)
        db.session.add(topic)
        db.session.commit()
        log_activity('Add Topic', f'Added Topic {topic.name} to Unit {topic.unit.number}')
        flash('Topic Added!', 'success')
        if request.args.get('next'):
            return redirect(request.args.get('next'))
            
        if current_user.role.name == 'Faculty':
             return redirect(url_for('main.faculty_dashboard'))
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/manage_syllabus.html', form=form, title='Add Topic')

@admin.route('/admin/edit/unit/<int:unit_id>', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Faculty')
def edit_unit(unit_id):
    unit = Unit.query.get_or_404(unit_id)
    # Security check: Single college setup
    pass
    form = UnitForm(obj=unit)
    form.subject.choices = [(s.id, s.name) for s in Subject.query.all()]
    if form.validate_on_submit():
        unit.number = form.number.data
        unit.subject_id = form.subject.data
        db.session.commit()
        log_activity('Edit Unit', f'Updated Unit {unit.number} in {unit.subject.name}')
        flash('Unit Updated!', 'success')
        return redirect(url_for('admin.dashboard'))
    form.subject.data = unit.subject_id
    return render_template('admin/manage_syllabus.html', form=form, title='Edit Unit', is_edit=True)

@admin.route('/admin/delete/unit/<int:unit_id>', methods=['POST'])
@login_required
@role_required('Admin', 'Faculty')
def delete_unit(unit_id):
    unit = Unit.query.get_or_404(unit_id)
    unit_num = unit.number
    sub_name = unit.subject.name
    db.session.delete(unit)
    db.session.commit()
    log_activity('Delete Unit', f'Deleted Unit {unit_num} from {sub_name}')
    flash(f'Unit {unit_num} Deleted!', 'success')
    return redirect(url_for('admin.dashboard'))

@admin.route('/admin/edit/topic/<int:topic_id>', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Faculty')
def edit_topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    # Security check: Single college setup
    pass
    form = TopicForm(obj=topic)
    form.unit.choices = [(u.id, f"{u.subject.name} - Unit {u.number}") for u in Unit.query.all()]
    if form.validate_on_submit():
        topic.name = form.name.data
        topic.unit_id = form.unit.data
        db.session.commit()
        log_activity('Edit Topic', f'Updated Topic {topic.name} in Unit {topic.unit.number}')
        flash('Topic Updated!', 'success')
        return redirect(url_for('admin.dashboard'))
    form.unit.data = topic.unit_id
    return render_template('admin/manage_syllabus.html', form=form, title='Edit Topic', is_edit=True)

@admin.route('/admin/delete/topic/<int:topic_id>', methods=['POST'])
@login_required
@role_required('Admin', 'Faculty')
def delete_topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    topic_name = topic.name
    unit_num = topic.unit.number
    db.session.delete(topic)
    db.session.commit()
    log_activity('Delete Topic', f'Deleted Topic {topic_name} from Unit {unit_num}')
    flash(f'Topic "{topic_name}" Deleted!', 'success')
    return redirect(url_for('admin.dashboard'))

@admin.route('/admin/upload_registry', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def upload_student_data():
    form = CSVUploadForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        # Determine strict parsing based on extension
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            
            # Expected columns: Register Number, Email
            # Normalize Headers
            df.columns = [c.strip() for c in df.columns]
            
            if 'Register Number' not in df.columns or 'Email' not in df.columns:
                flash('File must contain "Register Number" and "Email" columns.', 'danger')
                return redirect(url_for('admin.upload_student_data'))
            
            primary_college = College.query.first()
            for index, row in df.iterrows():
                reg_num = str(row['Register Number']).strip().upper()
                email = str(row['Email']).strip().lower()
                
                # Check for duplications
                exists = StudentRegistry.query.filter_by(register_number=reg_num, college_id=primary_college.id).first()
                if not exists:
                    registry = StudentRegistry(register_number=reg_num, email=email, college_id=primary_college.id)
                    db.session.add(registry)
                    count += 1
            
            db.session.commit()
            log_activity('Upload Registry', f'Uploaded {count} student records via {filename}')
            flash(f'Successfully uploaded {count} student records.', 'success')
            return redirect(url_for('admin.dashboard'))
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'danger')
            return redirect(url_for('admin.upload_student_data'))

    return render_template('admin/upload_registry.html', form=form)

@admin.route('/admin/add_student_registry', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def add_student_registry():
    from app.forms import SingleRegistryForm
    form = SingleRegistryForm()
    if form.validate_on_submit():
        reg_num = form.register_number.data.strip().upper()
        email = form.email.data.strip().lower()
        primary_college = College.query.first()
        
        # Duplication check
        exists = StudentRegistry.query.filter_by(register_number=reg_num, college_id=primary_college.id).first()
        if exists:
            flash(f'Student with Register Number {reg_num} already exists in registry.', 'warning')
        else:
            registry = StudentRegistry(register_number=reg_num, email=email, college_id=primary_college.id)
            db.session.add(registry)
            db.session.commit()
            log_activity('Add Registry Entry', f'Manually added {email} / {reg_num} to registry.')
            flash('Student added to authorized registry!', 'success')
            return redirect(url_for('admin.dashboard'))
            
    return render_template('admin/manage_syllabus.html', form=form, title='Add Student to Registry')

@admin.route('/admin/report/<int:user_id>')
@login_required
@role_required('Admin')
def user_report(user_id):
    import io
    import csv
    from app.models import ActivityLog
    
    user = User.query.get_or_404(user_id)
    # Security: Admin can only see reports of facultys
    if user.role.name != 'Faculty':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    logs = ActivityLog.query.filter_by(user_id=user.id).order_by(ActivityLog.timestamp.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Activity Report'])
    writer.writerow(['Username', user.username])
    writer.writerow(['Email', user.email])
    writer.writerow(['Role', user.role.name])
    writer.writerow([])
    writer.writerow(['Timestamp', 'Action', 'Details'])
    
    for log in logs:
        writer.writerow([log.timestamp.strftime('%Y-%m-%d %H:%M:%S'), log.action, log.details or ''])
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=activity_report_{user.username}.csv'
    response.headers['Content-Type'] = 'text/csv'
    
    log_activity('Generate Report', f'Generated activity report for faculty {user.username}')
    return response

@admin.route('/admin/download_logs/<role_name>')
@login_required
@role_required('Admin')
def download_logs(role_name):
    import io
    import csv
    from app.models import ActivityLog
    
    if role_name not in ['Faculty', 'Student']:
        flash('Invalid role specified.', 'danger')
        return redirect(url_for('admin.dashboard'))
        
    logs = ActivityLog.query.join(User).join(Role).filter(
        Role.name == role_name
    ).order_by(ActivityLog.timestamp.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Timestamp', 'User', 'Email', 'Action', 'Details'])
    
    for log in logs:
        writer.writerow([
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.user.username,
            log.user.email,
            log.action,
            log.details or ''
        ])
    
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename={role_name.lower()}_activity_logs.csv'
    response.headers['Content-Type'] = 'text/csv'
    
    log_activity('Download Bulk Logs', f'Downloaded bulk activity logs for {role_name}s')
    return response
