from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy import asc

from application.models import PlanningAuthority, LocalPlan

frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/', methods=['GET', 'POST'])
def index():
    planning_authorities = PlanningAuthority.query.all()
    if request.method == 'POST':
        return redirect(url_for('frontend.local_plan', planning_authority=request.form['local-authority-select']))
    return render_template('index.html', planning_authorities=planning_authorities)


@frontend.route('/local-plans/<planning_authority>')
def local_plan(planning_authority):
    pla = PlanningAuthority.query.get(planning_authority)
    plans = LocalPlan.query.filter_by(planning_authority_id=planning_authority).all()
    return render_template('local-plans.html', plans=plans, planning_authority=pla)
