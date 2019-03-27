# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located
in factory.py
"""


from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

from flask_migrate import Migrate
migrate = Migrate(db=db)

config = {
    'html': {'htmlmin': True,  'compress': True, 'cache': 'GET-60'},
    'json': {'htmlmin': False, 'compress': True, 'cache': False},
    'text': {'htmlmin': False, 'compress': True, 'cache': 'GET-60'},
    'trim_fragment': False,
}

from flask_optimize import FlaskOptimize
flask_optimize = FlaskOptimize(config=config)
