import json

from urllib.parse import urlencode
from application.auth.utils import requires_auth

from flask import (Blueprint,
                   render_template,
                   current_app,
                   session,
                   redirect,
                   url_for,
                   request)


auth = Blueprint('auth', __name__, template_folder='templates', url_prefix='/auth')


@auth.route('/userinfo')
@requires_auth
def dashboard():
    return render_template('userinfo.html',
                           userinfo=session['profile'],
                           userinfo_pretty=json.dumps(session['jwt_payload'], indent=4))


@auth.route('/login')
def login():
    session['redirect_url'] = request.args.get('redirect_url')
    auth0 = current_app.config['auth0']
    return auth0.authorize_redirect(redirect_uri=current_app.config['AUTH0_CALLBACK_URL'],
                                    audience=current_app.config['AUTH0_AUDIENCE'])


@auth.route('/logout')
def logout():
    session.clear()
    auth0 = current_app.config['auth0']
    params = {'returnTo': url_for('frontend.index', _external=True),
              'client_id': current_app.config['AUTH0_CLIENT_ID']}
    return redirect(auth0.api_base_url + '/v2/logout?' + urlencode(params))


@auth.route('/callback', methods=['GET', 'POST'])
def callback():
    auth0 = current_app.config['auth0']
    auth0.authorize_access_token()
    resp = auth0.get('userinfo')
    userinfo = resp.json()

    session['jwt_payload'] = userinfo
    session['profile'] = {
        'user_id': userinfo['sub'],
        'name': userinfo['name'],
        'picture': userinfo['picture'],
        'nickname': userinfo['nickname']
    }
    redirect_url = session.pop('redirect_url', None)
    if redirect_url is not None:
        return redirect(redirect_url)

    return redirect(url_for('auth.dashboard'))

