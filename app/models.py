from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Auth Models ---
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False) # Admin, Faculty, Student
    users = db.relationship('User', backref='role', lazy=True)

    def __repr__(self):
        return f"Role('{self.name}')"

class College(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    users = db.relationship('User', backref='college', lazy=True)
    student_registries = db.relationship('StudentRegistry', backref='college', lazy=True)

    @property
    def formatted_id(self):
        return f"CIDA{self.id:03d}"

class StudentRegistry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    register_number = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)
    is_registered = db.Column(db.Boolean, default=False)
    
    # Composite unique constraint to allow same reg num in diff colleges if needed, 
    # but usually reg num is unique per university. Let's assume unique per college for safety.
    __table_args__ = (db.UniqueConstraint('register_number', 'college_id', name='_college_regnum_uc'),)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=True) # Full Name
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    
    # New Fields
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=True)
    register_number = db.Column(db.String(50), nullable=True) # For Students
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    
    notes_uploaded = db.relationship('Note', backref='uploader', lazy=True)
    verifications = db.relationship('VerificationStatus', backref='verifier', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_online(self):
        if self.last_active:
            from datetime import timedelta
            return datetime.utcnow() < self.last_active + timedelta(minutes=5)
        return False

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

# --- Syllabus Models ---
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)
    semesters = db.relationship('Semester', backref='course', lazy=True, cascade="all, delete-orphan")

    __table_args__ = (db.UniqueConstraint('name', 'college_id', name='_course_college_uc'),)

class Semester(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False) # 1, 2, etc.
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    subjects = db.relationship('Subject', backref='semester', lazy=True, cascade="all, delete-orphan")

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    semester_id = db.Column(db.Integer, db.ForeignKey('semester.id'), nullable=False)
    units = db.relationship('Unit', backref='subject', lazy=True, cascade="all, delete-orphan")

class Unit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False) # 1, 2, etc.
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    topics = db.relationship('Topic', backref='unit', lazy=True, cascade="all, delete-orphan")

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
    notes = db.relationship('Note', backref='topic', lazy=True, cascade="all, delete-orphan")

# --- Note Models ---
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(200), nullable=True) # secure_filename or URL
    file_url = db.Column(db.String(500), nullable=True) # For external URLs
    material_type = db.Column(db.String(20), default='pdf') # pdf, docx, ppt, video, url
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_status = db.relationship('VerificationStatus', uselist=False, backref='note', lazy=True)

    __table_args__ = (db.UniqueConstraint('title', 'topic_id', 'college_id', name='_note_topic_title_uc'),)

class VerificationStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    note_id = db.Column(db.Integer, db.ForeignKey('note.id'), unique=True, nullable=False)
    verifier_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Who verified it
    status = db.Column(db.String(20), default='Pending') # Pending, Approved, Rejected
    comments = db.Column(db.Text, nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False) # e.g., 'Logged In', 'Uploaded Note'
    details = db.Column(db.Text, nullable=True) # Extra info like filename or IP (optional)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('activity_logs', lazy=True))

    def __repr__(self):
        return f"ActivityLog('{self.user.username}', '{self.action}', '{self.timestamp}')"
