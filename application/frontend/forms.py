from flask_wtf import FlaskForm
from wtforms import StringField, validators, IntegerField


class LocalDevelopmentSchemeURLForm(FlaskForm):
	url = StringField('Local development scheme URL', [validators.DataRequired()])


class LocalPlanURLForm(FlaskForm):
	url = StringField('Local plan URL')


class AddPlanForm(FlaskForm):
	start_year = IntegerField('Start year of plan', [validators.DataRequired()])

	# TODO need to add validator that checks if this id in use already