from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models import Course, Semester, Subject, Unit, Topic, College
from app.decorators import role_required

api = Blueprint('api', __name__)

# Fetch Operations
@api.route('/api/courses')
@login_required
def get_courses():
    courses = Course.query.all()
    return jsonify([{'id': c.id, 'name': c.name} for c in courses])

@api.route('/api/courses/<int:course_id>/semesters')
@login_required
def get_semesters(course_id):
    course = Course.query.get_or_404(course_id)
    # No college check needed
    pass
    semesters = Semester.query.filter_by(course_id=course_id).all()
    return jsonify([{'id': s.id, 'name': f"Semester {s.number}"} for s in semesters])

@api.route('/api/semesters/<int:semester_id>/subjects')
@login_required
def get_subjects(semester_id):
    sem = Semester.query.get_or_404(semester_id)
    # No college check needed
    pass
    subjects = Subject.query.filter_by(semester_id=semester_id).all()
    return jsonify([{'id': s.id, 'name': s.name} for s in subjects])

@api.route('/api/subjects/<int:subject_id>/units')
@login_required
def get_units(subject_id):
    sub = Subject.query.get_or_404(subject_id)
    # No college check needed
    pass
    units = Unit.query.filter_by(subject_id=subject_id).all()
    return jsonify([{'id': u.id, 'name': f"Unit {u.number}"} for u in units])

@api.route('/api/units/<int:unit_id>/topics')
@login_required
def get_topics(unit_id):
    unit = Unit.query.get_or_404(unit_id)
    # No college check needed
    pass
    topics = Topic.query.filter_by(unit_id=unit_id).all()
    return jsonify([{'id': t.id, 'name': t.name} for t in topics])

# Create Operations
@api.route('/api/courses', methods=['POST'])
@login_required
@role_required('Admin', 'Faculty')
def create_course():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400
    primary_college = College.query.first()
    course = Course(name=data['name'], college_id=primary_college.id)
    db.session.add(course)
    db.session.commit()
    return jsonify({'id': course.id, 'name': course.name, 'message': 'Course created!'})

@api.route('/api/semesters', methods=['POST'])
@login_required
@role_required('Admin', 'Faculty')
def create_semester():
    data = request.get_json()
    if not data or 'number' not in data or 'course_id' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    semester = Semester(number=data['number'], course_id=data['course_id'])
    db.session.add(semester)
    db.session.commit()
    return jsonify({'id': semester.id, 'name': f"Semester {semester.number}", 'message': 'Semester created!'})

@api.route('/api/subjects', methods=['POST'])
@login_required
@role_required('Admin', 'Faculty')
def create_subject():
    data = request.get_json()
    if not data or 'name' not in data or 'semester_id' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    subject = Subject(name=data['name'], semester_id=data['semester_id'])
    db.session.add(subject)
    db.session.commit()
    return jsonify({'id': subject.id, 'name': subject.name, 'message': 'Subject created!'})

@api.route('/api/units', methods=['POST'])
@login_required
@role_required('Admin', 'Faculty')
def create_unit():
    data = request.get_json()
    if not data or 'number' not in data or 'subject_id' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    unit = Unit(number=data['number'], subject_id=data['subject_id'])
    db.session.add(unit)
    db.session.commit()
    return jsonify({'id': unit.id, 'name': f"Unit {unit.number}", 'message': 'Unit created!'})

@api.route('/api/topics', methods=['POST'])
@login_required
@role_required('Admin', 'Faculty')
def create_topic():
    data = request.get_json()
    if not data or 'name' not in data or 'unit_id' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    topic = Topic(name=data['name'], unit_id=data['unit_id'])
    db.session.add(topic)
    db.session.commit()
    return jsonify({'id': topic.id, 'name': topic.name, 'message': 'Topic created!'})
