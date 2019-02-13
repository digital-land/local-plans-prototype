from flask import Blueprint, render_template
from sqlalchemy import asc

from application.models import PlanningAuthority, LocalPlan

frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/')
def index():
    planning_authorities = PlanningAuthority.query.all()
    return render_template('index.html', planning_authorities=planning_authorities)

@frontend.route('/local-plans/<planning_authority>')
def local_plan(planning_authority):
	pla = PlanningAuthority.query.get(planning_authority)
	grouped_plans = _group_plans(LocalPlan.query.filter_by(planning_authority_id=planning_authority).order_by(asc(LocalPlan.date)).all())
	return render_template('local-plans.html', grouped_plans=grouped_plans, planning_authority=pla)

def _group_plans(plans):
    grouped = []
    temp = []
    for plan in plans:
        if len(temp) == 0:
            temp.append(plan)
        elif temp[-1].local_plan == plan.local_plan:
            temp.append(plan)
        else:
            grouped.append(temp)
            temp = []
    grouped.append(temp)
    return grouped

