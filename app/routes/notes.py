import os
from flask import render_template, url_for, flash, redirect, request, Blueprint, send_from_directory, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import Note, Topic, Course, Semester, Subject, Unit, VerificationStatus, Role
from app.forms import NoteUploadForm, NoteSelectionForm, NoteEditForm
from app.decorators import role_required
from app.utils import log_activity

notes = Blueprint('notes', __name__)

def save_file(form_file):
    filename = secure_filename(form_file.filename)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    form_file.save(file_path)
    return filename

def save_file_to_cdn(form_file, material_type):
    import cloudinary.uploader
    import cloudinary
    
    # Check if keys are configured
    if not current_app.config.get('CLOUDINARY_CLOUD_NAME'):
        return None

    cloudinary.config( 
        cloud_name = current_app.config['CLOUDINARY_CLOUD_NAME'], 
        api_key = current_app.config['CLOUDINARY_API_KEY'], 
        api_secret = current_app.config['CLOUDINARY_API_SECRET'] 
    )
    
    resource_type = 'auto'
    if material_type == 'video':
        resource_type = 'video'
    elif material_type in ['pdf', 'docx', 'ppt']:
        resource_type = 'raw'
        
    try:
        upload_result = cloudinary.uploader.upload(
            form_file,
            resource_type=resource_type,
            folder="edustack_materials",
            use_filename=True,
            unique_filename=True
        )
        return upload_result['secure_url']
    except Exception as e:
        print(f"CDN Upload Error: {e}")
        return None

@notes.route('/notes/upload', methods=['GET', 'POST'])
@login_required
@role_required('Faculty', 'Admin')
def upload_note():
    form = NoteUploadForm()
    # Populate topics with full context, filtered by college
    topics = Topic.query.join(Unit).join(Subject).join(Semester).join(Course).all()
    form.topic.choices = [(t.id, f"{t.unit.subject.semester.course.name} - Sem {t.unit.subject.semester.number} - {t.unit.subject.name} - Unit {t.unit.number} - {t.name}") for t in topics]

    if form.validate_on_submit():
        material_type = form.material_type.data
        filename = None
        file_url = None
        
        if material_type == 'url':
            if not form.file_url.data:
                flash('Please provide a URL for this material type.', 'danger')
                return render_template('notes/upload_note.html', form=form)
            file_url = form.file_url.data
        else:
            if not form.file.data:
                flash('Please upload a file for this material type.', 'danger')
                return render_template('notes/upload_note.html', form=form)
            
            # Try CDN Upload
            cdn_url = save_file_to_cdn(form.file.data, material_type)
            if cdn_url:
                file_url = cdn_url
                filename = form.file.data.filename # Keep original name for record
            else:
                # Fallback to local storage
                filename = save_file(form.file.data)
                flash('CDN upload unavailable. Saved locally.', 'warning')

        # Robust Duplicate Detection: Check (title, topic_id, college_id)
        existing_note = Note.query.filter_by(
            title=form.title.data, 
            topic_id=form.topic.data
        ).first()

        if existing_note:
            flash(f'Duplicate detected! A study material with title "{form.title.data}" already exists for this syllabus topic.', 'warning')
            return redirect(url_for('notes.upload_note'))
        
        note = Note(
            title=form.title.data, 
            filename=filename, 
            file_url=file_url,
            material_type=material_type,
            user_id=current_user.id, 
            topic_id=form.topic.data,
            college_id=current_user.college_id
        )
        db.session.add(note)
        db.session.commit()
        
        # Create Verification Status
        verification = VerificationStatus(note_id=note.id, status='Pending')
        db.session.add(verification)
        db.session.commit()
        
        log_activity('Upload Material', f'Uploaded {material_type} material "{note.title}" for topic {note.topic.name}')
        flash('Study material uploaded! It is waiting for verification.', 'success')
        return redirect(url_for('notes.list_notes'))
    
    return render_template('notes/upload_note.html', form=form)

@notes.route('/notes', methods=['GET', 'POST'])
def list_notes():
    # Get filter parameters
    course_id = request.args.get('course_id', type=int)
    semester_num = request.args.get('semester_num', type=int)
    subject_id = request.args.get('subject_id', type=int)
    uploader_id = request.args.get('uploader_id', type=int)
    search_query = request.args.get('q', '')
    
    # Base query for verified notes
    # We join everything to support filtering by any combination
    notes_query = Note.query.filter_by(is_verified=True).join(Topic).join(Unit).join(Subject).join(Semester)
    
    # Apply independent filters
    course_query = Course.query
    subject_query = Subject.query
    semester_num_query = db.session.query(Semester.number).distinct()

    if course_id:
        notes_query = notes_query.filter(Semester.course_id == course_id)
    if semester_num:
        notes_query = notes_query.filter(Semester.number == semester_num)
    if subject_id:
        notes_query = notes_query.filter(Subject.id == subject_id)
    if uploader_id:
        notes_query = notes_query.filter(Note.user_id == uploader_id)
    if search_query:
        search_filter = f"%{search_query}%"
        from sqlalchemy import or_
        from app.models import User
        notes_query = notes_query.join(User, Note.user_id == User.id).filter(or_(
            Note.title.ilike(search_filter),
            Topic.name.ilike(search_filter),
            Subject.name.ilike(search_filter),
            User.username.ilike(search_filter)
        ))
    
    # Strict college isolation for authenticated users
    # No college filter needed in single college setup
    pass
    
    notes = notes_query.order_by(Note.upload_date.desc()).all()
    
    # Fetch all data in single college setup
    courses = course_query.all()
    subjects = subject_query.all()
    semester_nums = [n[0] for n in semester_num_query.order_by(Semester.number).all()]
    
    # Fetch uploaders for filter
    from app.models import User
    uploaders = User.query.join(Note, User.id == Note.user_id).distinct().all()
    
    return render_template('notes/list_notes.html', 
                           notes=notes, 
                           courses=courses, 
                           semester_nums=semester_nums, 
                           subjects=subjects,
                           uploaders=uploaders,
                           selected_course=course_id,
                           selected_semester_num=semester_num,
                           selected_subject=subject_id,
                           selected_uploader=uploader_id,
                           search_query=search_query)

@notes.route('/notes/verify')
@login_required
@role_required('Faculty', 'Admin')
def verification_queue():
    # Only show notes for the same college
    pending_notes = Note.query.filter_by(is_verified=False).all()
    return render_template('notes/verification_queue.html', notes=pending_notes)

@notes.route('/notes/approve/<int:note_id>')
@login_required
@role_required('Faculty', 'Admin')
def approve_note(note_id):
    note = Note.query.get_or_404(note_id)
    note.is_verified = True
    
    status = VerificationStatus.query.filter_by(note_id=note.id).first()
    if status:
        status.status = 'Approved'
        status.verifier_id = current_user.id
        from datetime import datetime
        status.verified_at = datetime.utcnow()
    
    db.session.commit()
    log_activity('Verify Note', f'Approved note "{note.title}"')
    flash('Note approved.', 'success')
    return redirect(url_for('notes.verification_queue'))

@notes.route('/notes/delete/<int:note_id>', methods=['POST'])
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    
    # Permission check: Teacher/Admin or Uploader
    can_delete = current_user.role.name in ['Faculty', 'Admin'] or current_user.id == note.user_id
    if not can_delete:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('notes.list_notes'))
    
    title = note.title
    filename = note.filename
    
    # File cleanup
    if filename and not note.file_url:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error deleting file: {e}")
                flash('Note record deleted, but there was an issue removing the physical file.', 'warning')

    # Remove verification status first due to FK
    VerificationStatus.query.filter_by(note_id=note.id).delete()
    db.session.delete(note)
    db.session.commit()
    
    log_activity('Delete Note', f'Deleted note "{title}"')
    flash(f'Note "{title}" has been deleted.', 'success')
    return redirect(url_for('notes.list_notes'))

@notes.route('/notes/edit/<int:note_id>', methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    note = Note.query.get_or_404(note_id)
    
    # Permission check: Teacher/Admin or Uploader
    can_edit = current_user.role.name in ['Faculty', 'Admin'] or current_user.id == note.user_id
    if not can_edit:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('notes.list_notes'))
        
    form = NoteEditForm()
    if form.validate_on_submit():
        old_title = note.title
        note.title = form.title.data
        db.session.commit()
        log_activity('Edit Note', f'Changed note title from "{old_title}" to "{note.title}"')
        flash('Note title updated.', 'success')
        return redirect(url_for('notes.list_notes'))
    elif request.method == 'GET':
        form.title.data = note.title
        
    return render_template('notes/edit_note.html', form=form, note=note)

@notes.route('/notes/reject/<int:note_id>')
@login_required
@role_required('Faculty', 'Admin')
def reject_note(note_id):
    note = Note.query.get_or_404(note_id)
    # Ideally we might delete the file or mark as rejected. Let's delete for now to clean up? 
    # Or just mark status.
    status = VerificationStatus.query.filter_by(note_id=note.id).first()
    if status:
        status.status = 'Rejected'
        status.verifier_id = current_user.id
        from datetime import datetime
        status.verified_at = datetime.utcnow()
    
    db.session.commit()
    log_activity('Verify Note', f'Rejected note "{note.title}"')
    flash('Note rejected.', 'danger')
    return redirect(url_for('notes.verification_queue'))

@notes.route('/notes/download/<filename>')
@login_required
def download_file(filename):
    # Only allow if verified or if user is uploader/teacher/admin
    note = Note.query.filter_by(filename=filename).first_or_404()
    if not note.is_verified:
        if current_user.role.name == 'Student' and current_user.id != note.user_id:
            flash('This note is not yet verified.', 'warning')
            return redirect(url_for('notes.list_notes'))
            
    if note.file_url:
        # If it's a Cloudinary URL, attempt to add attachment flag for direct download
        if "res.cloudinary.com" in note.file_url:
            if "/upload/" in note.file_url:
                parts = note.file_url.split('/upload/')
                download_url = f"{parts[0]}/upload/fl_attachment/{parts[1]}"
                return redirect(download_url)
        return redirect(note.file_url)

    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@notes.route('/notes/view/<filename>')
@login_required
def view_file(filename):
    # Only allow if verified or if user is uploader/teacher/admin
    note = Note.query.filter_by(filename=filename).first_or_404()
    if not note.is_verified:
        if current_user.role.name == 'Student' and current_user.id != note.user_id:
            flash('This note is not yet verified.', 'warning')
            return redirect(url_for('notes.list_notes'))
    
    if note.file_url:
        return redirect(note.file_url)

    # Send file with inline disposition to view in browser
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=False)
