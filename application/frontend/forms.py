from flask_wtf import FlaskForm
from wtforms import StringField, validators

class PlanningPolicyURLForm(FlaskForm):
	url = StringField('Planning policy URL', [validators.DataRequired()])
