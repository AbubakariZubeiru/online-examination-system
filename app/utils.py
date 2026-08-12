from functools import wraps
from flask import abort
from flask_login import current_user


def role_required(*roles):
    """Restrict a view to users whose .role is in `roles`."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                abort(403)
            return view_func(*args, **kwargs)
        return wrapped
    return decorator
