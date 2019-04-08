from flask_wtf import FlaskForm
from wtforms import StringField, validators, IntegerField, HiddenField, SelectMultipleField


class LocalDevelopmentSchemeURLForm(FlaskForm):
	url = StringField('Local development scheme URL', [validators.DataRequired()])


class LocalPlanURLForm(FlaskForm):
	url = StringField('Local plan URL')


class AddPlanForm(FlaskForm):
	title = StringField('Plan title', [validators.DataRequired()])
	start_year = IntegerField('Start year', [validators.DataRequired()])
	end_year = IntegerField('End year', [validators.DataRequired()])
	planning_authority = HiddenField()


class MakeJointPlanForm(FlaskForm):
	planning_authorities = SelectMultipleField('Select one or more planning authorities', [validators.DataRequired()])

