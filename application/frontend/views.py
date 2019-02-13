from flask import Blueprint, render_template

from application.models import PlanningAuthority

frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/')
def index():
    planning_authorities = PlanningAuthority.query.all()
    return render_template('index.html', planning_authorities=planning_authorities)



@frontend.route('/local-plans/<planning_authority>')
def local_plan(planning_authority):
    planning_authority = PlanningAuthority.query.get(planning_authority)
    return render_template('local-plans.html', planning_authority=planning_authority)