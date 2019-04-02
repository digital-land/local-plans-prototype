# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template
from flask.cli import load_dotenv

from application.filters import (
    format_date,
    format_month_and_year,
    format_date_from_str,
    format_fact,
    format_percent,
    return_percent,
    format_year
)


if os.environ.get('FLASK_ENV') == 'production':
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path)


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
        return None


def register_blueprints(app):
    from application.frontend.views import frontend
    app.register_blueprint(frontend)


def register_extensions(app):
    from application.extensions import db
    db.init_app(app)

    from application.models import PlanningAuthority
    from application.extensions import migrate
    migrate.init_app(app=app)

    from flask_sslify import SSLify
    sslify = SSLify(app)

def register_commands(app):
    from application.commands import load, clear, set_ons_codes, load_hdt, load_geojson
    app.cli.add_command(load, name='load')
    app.cli.add_command(clear, name='clear')
    app.cli.add_command(set_ons_codes, name='set_ons')
    app.cli.add_command(load_hdt, name='load_hdt')
    app.cli.add_command(load_geojson, name='load_geojson')


def register_filters(app):
    app.add_template_filter(format_date)
    app.add_template_filter(format_month_and_year)
    app.add_template_filter(format_date_from_str)
    app.add_template_filter(format_fact)
    app.add_template_filter(format_percent)
    app.add_template_filter(return_percent)
    app.add_template_filter(format_year)


def register_context_processors(app):

    @app.context_processor
    def _inject_asset_path():
        return {'assetPath': '/static'}

