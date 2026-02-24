from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Optional, NumberRange
from flask_wtf.file import FileField, FileAllowed
from app.models import User

class RegistrationForm(FlaskForm):
    role = SelectField('Role', choices=[('Student', 'Student'), ('Faculty', 'Faculty')], validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    name = StringField('Full Name', validators=[Optional(), Length(max=120)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    register_number = StringField('Register Number', validators=[Optional()]) # Used for Student
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class CSVUploadForm(FlaskForm):
    file = FileField('Upload Student Registry (CSV/Excel)', validators=[DataRequired(), FileAllowed(['csv', 'xlsx'], 'CSV or Excel only!')])
    submit = SubmitField('Upload Bulk Data')

class SingleRegistryForm(FlaskForm):
    register_number = StringField('Register Number', validators=[DataRequired(), Length(max=50)])
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    submit = SubmitField('Add to Registry')

class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[
        ('Student', 'Student'), 
        ('Faculty', 'Faculty'), 
        ('Admin', 'Admin')
    ], validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class CollegeForm(FlaskForm):
    name = StringField('College Name', validators=[DataRequired()])
    submit = SubmitField('Add College')

class CourseForm(FlaskForm):
    name = StringField('Course Name', validators=[DataRequired()])
    submit = SubmitField('Add Course')

class SemesterForm(FlaskForm):
    number = IntegerField('Semester Number', validators=[DataRequired(), NumberRange(min=1)], default=1, render_kw={"min": "1"})
    course = SelectField('Course', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Semester')

class SubjectForm(FlaskForm):
    name = StringField('Subject Name', validators=[DataRequired()])
    semester = SelectField('Semester', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Subject')

class UnitForm(FlaskForm):
    number = IntegerField('Unit Number', validators=[DataRequired(), NumberRange(min=1)], default=1, render_kw={"min": "1"})
    subject = SelectField('Subject', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Unit')

class TopicForm(FlaskForm):
    name = StringField('Topic Name', validators=[DataRequired()])
    unit = SelectField('Unit', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Topic')


class NoteSelectionForm(FlaskForm):
    course = SelectField('Course', coerce=int, validators=[DataRequired()])
    semester = SelectField('Semester', coerce=int, validators=[DataRequired()])
    subject = SelectField('Subject', coerce=int, validators=[DataRequired()])
    unit = SelectField('Unit', coerce=int, validators=[DataRequired()])
    topic = SelectField('Topic', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Filter')

class NoteUploadForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    topic = SelectField('Topic', coerce=int, validators=[DataRequired()], validate_choice=False) # Dynamic AJAX
    material_type = SelectField('Type', choices=[
        ('pdf', 'PDF Document'),
        ('docx', 'Word Document'),
        ('ppt', 'PowerPoint'),
        ('video', 'Video (MP4/MKV)'),
        ('url', 'External URL / Link')
    ], default='pdf', validators=[DataRequired()])
    file = FileField('Upload File', validators=[Optional(), FileAllowed(['pdf', 'docx', 'pptx', 'ppt', 'mp4', 'mkv'], 'Allowed formats: PDF, DOCX, PPT, MP4, MKV')])
    file_url = StringField('External URL', validators=[Optional()])
    submit = SubmitField('Upload Study Material')

class NoteEditForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    submit = SubmitField('Update Title')

