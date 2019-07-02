# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template
from flask.cli import load_dotenv

from application.filters import (
    format_date,
    format_month_and_year,
    format_date_from_str,
    format_housing_number_type,
    format_percent,
    return_percent,
    format_year,
    format_housing_number,
    big_number
)


load_dotenv()


def create_app(config_filename):

    if os.environ.get('SENTRY_DSN') is not None:

        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration

        sentry_sdk.init(
            dsn=os.environ.get('SENTRY_DSN'),
            integrations=[FlaskIntegration()]
        )

    app = Flask(__name__)
    app.config.from_object(config_filename)
    register_errorhandlers(app)
    register_blueprints(app)
    register_extensions(app)
    register_commands(app)
    register_filters(app)
    register_context_processors(app)
    return app


def register_errorhandlers(app):
    def render_error(error):
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, 'code', 500)
        return render_template("error/{0}.html".format(error_code)), error_code
    for errcode in [400, 401, 404, 500]:
        app.errorhandler(errcode)(render_error)


def register_blueprints(app):
    from application.frontend.views import frontend
    app.register_blueprint(frontend)

    from application.auth.views import auth
    app.register_blueprint(auth)


def register_extensions(app):
    from application.extensions import db
    db.init_app(app)

    from application.models import PlanningAuthority
    from application.extensions import migrate
    migrate.init_app(app=app)

    from flask_sslify import SSLify
    sslify = SSLify(app)

    from application.extensions import OAuth
    oauth = OAuth(app)

    auth0 = oauth.register(
        'auth0',
        client_id=app.config['AUTH0_CLIENT_ID'],
        client_secret=app.config['AUTH0_CLIENT_SECRET'],
        api_base_url=app.config['AUTH0_BASE_URL'],
        access_token_url=f"{app.config['AUTH0_BASE_URL']}/oauth/token",
        authorize_url=f"{app.config['AUTH0_BASE_URL']}/authorize",
        client_kwargs={
            'scope': 'openid profile',
        },
    )

    app.config['auth0'] = auth0


def register_commands(app):
    from application.commands import cache_docs_in_s3, pins_update
    app.cli.add_command(cache_docs_in_s3, name='cache_docs_in_s3')
    app.cli.add_command(pins_update, name='pins_update')


def register_filters(app):
    app.add_template_filter(format_date)
    app.add_template_filter(format_month_and_year)
    app.add_template_filter(format_date_from_str)
    app.add_template_filter(format_housing_number_type)
    app.add_template_filter(format_percent)
    app.add_template_filter(return_percent)
    app.add_template_filter(format_year)
    app.add_template_filter(format_housing_number)
    app.add_template_filter(big_number)


def register_context_processors(app):

    @app.context_processor
    def _inject_asset_path():
        return {'assetPath': '/static'}

