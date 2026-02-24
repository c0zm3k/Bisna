from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required
from app.decorators import role_required

main = Blueprint('main', __name__)

@main.route('/faculty/logs')
@login_required
@role_required('Faculty')
def view_student_logs():
    # Filter logs for 'Student' role users
    from app.models import ActivityLog, User, Role
    logs = ActivityLog.query.join(User).join(Role).filter(
        Role.name == 'Student'
    ).order_by(ActivityLog.timestamp.desc()).all()
    return render_template('faculty/logs.html', logs=logs, title='Student Activity Logs')

@main.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role.name == 'Admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role.name == 'Faculty':
            return redirect(url_for('main.faculty_dashboard'))
        else:
            return redirect(url_for('notes.list_notes'))
    return render_template('index.html') # Landing page

@main.route('/faculty/dashboard')
@login_required
def faculty_dashboard():
    if current_user.role.name != 'Faculty':
        return redirect(url_for('main.index'))
    from app.models import Course, Note, Role, User
    courses = Course.query.all()
    
    # Fetch verified students for THIS college
    verified_students = User.query.join(Role).filter(
        User.is_verified == True,
        Role.name == 'Student'
    ).all()

    # Fetch notes
    verified_notes = Note.query.filter_by(is_verified=True).all()

    pending_notes = Note.query.filter_by(is_verified=False).all()

    return render_template('faculty/dashboard.html', 
                           courses=courses, 
                           verified_students=verified_students,
                           verified_notes=verified_notes,
                           pending_notes=pending_notes)

@main.route('/student/report/<int:user_id>')
@login_required
@role_required('Faculty', 'Admin')
def student_report(user_id):
    import io
    import csv
    from flask import make_response
    from app.models import ActivityLog, User
    
    user = User.query.get_or_404(user_id)
    # Security: Faculty can only see reports of students in their college
    # Security: Faculty can only see reports of students
    if user.role.name != 'Student':
        from flask import flash
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('main.faculty_dashboard'))
    
    logs = ActivityLog.query.filter_by(user_id=user.id).order_by(ActivityLog.timestamp.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student Activity Report'])
    writer.writerow(['Username', user.username])
    writer.writerow(['Register Number', user.register_number or 'N/A'])
    writer.writerow([])
    writer.writerow(['Timestamp', 'Action', 'Details'])
    
    for log in logs:
        writer.writerow([log.timestamp.strftime('%Y-%m-%d %H:%M:%S'), log.action, log.details or ''])
    
    output.seek(0)
    from flask import make_response
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=student_report_{user.username}.csv'
    response.headers['Content-Type'] = 'text/csv'
    
    from app.utils import log_activity
    log_activity('Generate Report', f'Generated activity report for student {user.username}')
    return response

@main.route('/faculty/download_student_logs')
@login_required
@role_required('Faculty')
def download_student_logs():
    import io
    import csv
    from app.models import ActivityLog, User, Role
    from flask import make_response
    
    logs = ActivityLog.query.join(User).join(Role).filter(
        Role.name == 'Student'
    ).order_by(ActivityLog.timestamp.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Timestamp', 'Student', 'Email', 'Action', 'Details'])
    
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
    response.headers['Content-Disposition'] = 'attachment; filename=student_activity_logs.csv'
    response.headers['Content-Type'] = 'text/csv'
    
    from app.utils import log_activity
    log_activity('Download Bulk Logs', 'Faculty downloaded bulk activity logs for students')
    return response

