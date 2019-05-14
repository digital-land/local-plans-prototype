from functools import wraps

from flask import session, url_for, request, current_app
from werkzeug.utils import redirect


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'profile' not in session and current_app.config['AUTHENTICATION_ON']:
            return redirect(url_for('auth.login', redirect_url=request.path))
        return f(*args, **kwargs)
    return decorated


def get_current_user():
    if session.get('profile') is not None:
        if session['profile'].get('nickname') is not None:
            return session['profile'].get('nickname')
        else:
            return session['profile'].get('name')
    else:
        return None