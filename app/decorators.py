from functools import wraps
from flask import abort
from flask_login import current_user

def role_required(*role_names):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return abort(403)
            
            # Check if user's role is in the allowed roles
            if current_user.role.name not in role_names:
                abort(403)
            
            # Enforce verification
            if not current_user.is_verified:
                abort(403, description="Your account is pending verification.")
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return role_required('Admin')(f)
