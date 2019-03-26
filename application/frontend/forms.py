from flask_wtf import FlaskForm
from wtforms import StringField, validators, IntegerField, ValidationError, HiddenField

from application.models import LocalPlan


class LocalDevelopmentSchemeURLForm(FlaskForm):
	url = StringField('Local development scheme URL', [validators.DataRequired()])


class LocalPlanURLForm(FlaskForm):
	url = StringField('Local plan URL')


class AddPlanForm(FlaskForm):
	start_year = IntegerField('Start year of plan', [validators.DataRequired()])
	planning_authority = HiddenField()

	def validate_start_year(form, field):
		plan_id = f'{form.planning_authority.data}-{field.data}'
		plan = LocalPlan.query.filter_by(local_plan=plan_id).first()
		if plan is not None:
			raise ValidationError(f'Plan with id {plan_id} already exists.')
