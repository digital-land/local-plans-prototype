from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from sqlalchemy import asc

from application.extensions import db
from application.models import PlanningAuthority, LocalPlan, PlanDocument

frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@frontend.route('/local-plans', methods=['GET', 'POST'])
def list_all():
    planning_authorities = PlanningAuthority.query.all()
    if request.method == 'POST':
        return redirect(url_for('frontend.local_plan', planning_authority=request.form['local-authority-select']))
    return render_template('list.html', planning_authorities=planning_authorities)


@frontend.route('/local-plans/<planning_authority>')
def local_plan(planning_authority):
    pla = PlanningAuthority.query.get(planning_authority)
    plans = LocalPlan.query.filter_by(planning_authority_id=planning_authority).all()
    return render_template('local-plans.html', plans=plans, planning_authority=pla)


@frontend.route('/local-plans/<planning_authority>/<local_plan>', methods=['POST'])
def add_document_to_plan(planning_authority, local_plan):
    plan = LocalPlan.query.filter_by(planning_authority_id=planning_authority, local_plan=local_plan).one()

    if request.json.get('url') is not None:
        url = request.json['url']
        document = PlanDocument(url=url)
        plan.plan_documents.append(document)
        db.session.add(plan)
        db.session.commit()
        remove_url = url_for('frontend.remove_document_from_plan', document_id=str(document.id), local_plan=plan.local_plan)
        resp = {'OK': 200, 'url': url, 'document_id': str(document.id), 'remove_url': remove_url}
    elif request.json.get('notes') is not None:
        notes = request.json.get('notes')
        plan.notes = notes
        db.session.add(plan)
        db.session.commit()
        resp = {'OK': 200, 'notes': notes}
    elif request.json.get('housing_units') is not None:
        housing_units = request.json.get('housing_units')
        plan.number_of_houses = housing_units
        db.session.add(plan)
        db.session.commit()
        resp = {'OK': 200, 'housing_units': housing_units}

    return jsonify(resp)


@frontend.route('/local-plans/<local_plan>/document/<document_id>', methods=['DELETE'])
def remove_document_from_plan(local_plan, document_id):
    plan = PlanDocument.query.filter_by(local_plan_id=local_plan, id=document_id).one()
    db.session.delete(plan)
    db.session.commit()
    return jsonify({204: 'No Contest'})


@frontend.route('/local-plans/add-document', methods=['POST'])
def add_document_for_checking():
    print(request.json)
    return redirect(url_for('frontend.index'))


@frontend.route('/local-plans/check')
def lucky_dip():
    import random
    query = db.session.query(PlanningAuthority)
    row_count = int(query.count())
    pla = query.offset(int(row_count * random.random())).first()
    return render_template('lucky-dip.html', planning_authority=pla)
