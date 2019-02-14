from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from sqlalchemy import asc

from application.extensions import db
from application.models import PlanningAuthority, LocalPlan, PlanDocument

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


@frontend.route('/local-plans/<planning_authority>/<local_plan>', methods=['POST'])
def add_document_to_plan(planning_authority, local_plan):
    plan = LocalPlan.query.filter_by(planning_authority_id=planning_authority, local_plan=local_plan).one()
    url = request.json['url']
    document = PlanDocument(url=url)
    plan.plan_documents.append(document)
    db.session.add(plan)
    db.session.commit()

    return jsonify({'OK': 200, 'url': url})
