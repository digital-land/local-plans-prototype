# -*- coding: utf-8 -*-
import os


class Config:
    CONFIG_ROOT = os.path.abspath(os.path.dirname(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(CONFIG_ROOT, os.pardir))
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    S3_REGION = os.getenv('S3_REGION')
    S3_BUCKET = os.getenv('S3_BUCKET')
    MAPBOX_TOKEN = os.getenv('MAPBOX_TOKEN')


class DevelopmentConfig(Config):
    DEBUG = True
    WTF_CSRF_ENABLED = True


class TestConfig(Config):
    TESTING = True
