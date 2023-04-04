# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located
in factory.py
"""


from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from flask_migrate import Migrate

migrate = Migrate(db=db)


from authlib.integrations.flask_client import OAuth
