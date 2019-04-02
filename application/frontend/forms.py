from flask_wtf import FlaskForm
from wtforms import StringField, validators, IntegerField, ValidationError, HiddenField

from application.models import LocalPlan


class LocalDevelopmentSchemeURLForm(FlaskForm):
	url = StringField('Local development scheme URL', [validators.DataRequired()])


class LocalPlanURLForm(FlaskForm):
	url = StringField('Local plan URL')


class AddPlanForm(FlaskForm):
	title = StringField('Plan title', [validators.DataRequired()])
	start_year = IntegerField('Start year of plan', [validators.DataRequired()])
	end_year = IntegerField('End year of plan', [validators.DataRequired()])
	planning_authority = HiddenField()
