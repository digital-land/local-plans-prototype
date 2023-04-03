# -*- coding: utf-8 -*-
import os


def _to_boolean(val):
    if val is not None and val.lower() in ['true', 't', 'on', 'y', 'yes']:
        return True
    return False


class Config:
    CONFIG_ROOT = os.path.abspath(os.path.dirname(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(CONFIG_ROOT, os.pardir))
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    S3_REGION = os.getenv('S3_REGION')
    S3_BUCKET = os.getenv('S3_BUCKET')
    MAPBOX_TOKEN = os.getenv('MAPBOX_TOKEN')
    AUTH0_CLIENT_ID = os.getenv('AUTH0_CLIENT_ID')
    AUTH0_CLIENT_SECRET = os.getenv('AUTH0_CLIENT_SECRET')
    AUTH0_DOMAIN = os.getenv('AUTH0_DOMAIN')
    AUTH0_CALLBACK_URL = os.getenv('AUTH0_CALLBACK_URL')
    AUTH0_BASE_URL = f"https://{AUTH0_DOMAIN}"
    AUTH0_AUDIENCE = f"{AUTH0_BASE_URL}/userinfo"
    AUTHENTICATION_ON = _to_boolean(os.environ.get('AUTHENTICATION_ON'))
    INCLUDE_PINS = _to_boolean(os.environ.get('INCLUDE_PINS'))


class DevelopmentConfig(Config):
    DEBUG = True
    WTF_CSRF_ENABLED = True

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/local_plans_test'
