from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from app import db
from app.models import User, Role, College, StudentRegistry
from app.forms import RegistrationForm, LoginForm
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint('auth', __name__)

@auth.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    
    if form.validate_on_submit():
        role = Role.query.filter_by(name=form.role.data).first()
        if not role:
            flash('Error: Roles not initialized.', 'danger')
            return redirect(url_for('auth.register'))
            
        hashed_password = generate_password_hash(form.password.data)
        
        # Check for existing user credentials
        existing_user = User.query.filter((User.email == form.email.data.strip().lower()) | 
                                         (User.username == form.username.data.strip())).first()
        if existing_user:
            if existing_user.email == form.email.data.strip().lower():
                flash('Email address is already in use.', 'danger')
            else:
                flash('Username is already taken.', 'danger')
            return render_template('auth/register.html', title='Register', form=form)

        # Single College Architecture: Always use the first seeded college
        primary_college = College.query.first()
        if not primary_college:
            flash('Error: Institution not initialized.', 'danger')
            return redirect(url_for('auth.register'))
        
        college_id = primary_college.id

        # Student specific logic
        if role.name == 'Student':
            email = form.email.data.strip().lower()
            reg_num = form.register_number.data.strip().upper()
            # Check registry based on BOTH Email and Register Number
            registry_entry = StudentRegistry.query.filter_by(
                email=email, 
                register_number=reg_num, 
                college_id=college_id
            ).first()
            
            if not registry_entry:
                flash('Registration failed: Email or Register Number not found in the College Registry.', 'danger')
                return render_template('auth/register.html', title='Register', form=form)
                
            if registry_entry.is_registered:
                flash('This student is already registered.', 'warning')
                return render_template('auth/register.html', title='Register', form=form)

            # Valid student - Create user
            username = (form.username.data or "").strip()
            name = (form.name.data or "").strip()
            user = User(username=username, name=name, email=email, password_hash=hashed_password, role=role,
                        college_id=college_id, register_number=reg_num, is_verified=True)
            
            registry_entry.is_registered = True
            db.session.add(user)
            db.session.commit()
            flash('Account created! You are verified and can log in.', 'success')
            return redirect(url_for('auth.login'))

        # Faculty logic
        elif role.name == 'Faculty':
             username = form.username.data.strip()
             email = form.email.data.strip().lower()
             name = (form.name.data or "").strip()
             
             user = User(username=username, name=name, email=email, password_hash=hashed_password, role=role,
                        college_id=college_id, is_verified=False)
             db.session.add(user)
             db.session.commit()
             flash(f'Account created! Please wait for verification.', 'info')
             return redirect(url_for('auth.login'))
            
    return render_template('auth/register.html', title='Register', form=form)

# Admin registration handled in main register route

@auth.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        
        if user and check_password_hash(user.password_hash, form.password.data):
             # Verify Role Match
            if user.role.name != form.role.data:
                 # Perfect match expected.
                 flash(f'Role mismatch. You are registered as a {user.role.name}, not {form.role.data}.', 'danger')
                 return render_template('auth/login.html', title='Login', form=form)

            login_user(user, remember=form.remember.data)
            
            # Log Activity
            from app.utils import log_activity
            log_activity('Login', f'User {user.username} logged in.')
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('auth/login.html', title='Login', form=form)

@auth.route("/logout")
def logout():
    if current_user.is_authenticated:
        from app.utils import log_activity
        log_activity('Logout', f'User {current_user.username} logged out.')
    logout_user()
    return redirect(url_for('main.index'))

@auth.route("/profile")
@login_required
def profile():
    return render_template('auth/profile.html', title='User Profile')
