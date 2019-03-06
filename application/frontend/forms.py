from flask_wtf import FlaskForm
from wtforms import StringField, validators


class LocalDevelopmentSchemeURLForm(FlaskForm):
	url = StringField('Local development scheme URL', [validators.DataRequired()])


class LocalPlanURLForm(FlaskForm):
	url = StringField('Local plan URL')


class DocumentURLForm(FlaskForm):
	url = StringField('URL of plan, scheme or emerging plan document', [validators.DataRequired()])
