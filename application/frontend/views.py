from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from sqlalchemy import asc

from application.extensions import db
from application.models import PlanningAuthority, LocalPlan, PlanDocument, EmergingPlanDocument, Fact, FactType, \
    EmergingFactType
from application.frontend.forms import PlanningPolicyURLForm, LocalPlanURLForm

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
    return render_template('local-plans.html',
                           planning_authority=pla,
                           fact_types=FactType,
                           emerging_fact_types=EmergingFactType)


@frontend.route('/start-collecting-data')
def start_collecting_data():
    return render_template('collecting-data-start-page.html')


@frontend.route('/local-plans/<planning_authority>/<local_plan>', methods=['POST'])
def add_document_to_plan(planning_authority, local_plan):
    plan = LocalPlan.query.get(local_plan)

    if request.json.get('url') is not None:
        url = request.json['url']
        document = PlanDocument(url=url)
        plan.plan_documents.append(document)
        db.session.add(plan)
        db.session.commit()
        remove_url = url_for('frontend.remove_document_from_plan', document=str(document.id), local_plan=plan.local_plan)
        resp = {'OK': 200, 'url': url, 'document_id': str(document.id), 'remove_url': remove_url}
    else:
        resp = {'OK': 200}

    return jsonify(resp)


@frontend.route('/local-plans/<planning_authority>/<local_plan>/<document>', methods=['POST'])
def add_fact_to_document(planning_authority, local_plan, document):

    plan_document = PlanDocument.query.filter_by(id=document, local_plan_id=local_plan).one()

    if request.json.get('fact') is not None:
        fact = request.json['fact']
        fact = Fact(number=fact.get('number'), notes=fact.get('notes'))
        plan_document.facts.append(fact)
        db.session.add(plan_document)
        db.session.commit()
        remove_url = url_for('frontend.remove_fact_from_document', document=str(plan_document.id), fact=fact.id)
        resp = {'OK': 200, 'fact': fact.to_dict(), 'remove_url': remove_url}
    else:
        resp = {'OK': 200}

    return jsonify(resp)


@frontend.route('/local-plans/<document>/<fact>', methods=['GET', 'DELETE'])
def remove_fact_from_document(document, fact):
    fact = Fact.query.filter_by(id=fact, plan_document_id=document).one();
    db.session.delete(fact)
    db.session.commit()
    # do something
    return jsonify({204: 'No Content'})


@frontend.route('/local-plans/<planning_authority>/update-local-scheme-url', methods=['GET', 'POST'])
def update_local_scheme_url(planning_authority):
    pla = PlanningAuthority.query.get(planning_authority)
    form = PlanningPolicyURLForm(url=pla.local_scheme_url)

    if form.validate_on_submit():
        pla.local_scheme_url = form.url.data
        db.session.add(pla)
        db.session.commit()
        return redirect(url_for('frontend.local_plan', planning_authority=pla.id))

    return render_template('update-scheme-url.html', planning_authority=pla, form=form)


@frontend.route('/local-plans/<planning_authority>/<local_plan>/update-plan-url', methods=['GET', 'POST'])
def update_local_plan_url(planning_authority, local_plan):
    pla = PlanningAuthority.query.get(planning_authority)
    plan = LocalPlan.query.get(local_plan)
    form = LocalPlanURLForm(url=plan.planning_policy_url)
    if form.validate_on_submit():
        plan.planning_policy_url = form.url.data
        db.session.add(pla)
        db.session.commit()
        return redirect(url_for('frontend.local_plan', planning_authority=pla.id))

    return render_template('update-local-plan-url.html', planning_authority=pla, local_plan=plan, form=form)


@frontend.route('/local-plans/<local_plan>/document/<document>', methods=['DELETE'])
def remove_document_from_plan(local_plan, document):
    plan = PlanDocument.query.filter_by(local_plan_id=local_plan, id=document).one()
    db.session.delete(plan)
    db.session.commit()
    return jsonify({204: 'No Content'})


def _get_planning_authority_url(documents):
    from urllib.parse import urlparse
    if documents:
        url = documents[0]
        url = urlparse(url)
        return f'{url.scheme}://{url.netloc}'
    else:
        return None


@frontend.route('/local-plans/add-document', methods=['POST'])
def add_document_for_checking():
    documents = request.json['documents']
    active_plan_id = request.json.get('active_plan')
    website = (request.json.get('active_page_origin') if request.json.get('active_page_origin') is not None else _get_planning_authority_url(documents))

    if active_plan_id == 'localDevelopmentScheme' and website is not None:

        pla = PlanningAuthority.query.filter_by(website=website).one()
        for doc in documents:
            if EmergingPlanDocument.query.filter_by(url=doc).first() is None:
                pla.emerging_plan_documents.append(EmergingPlanDocument(url=doc))

        db.session.add(pla)
        db.session.commit()

        # TODO get the actual contents and store in s3
        resp = {'OK': 200, 'check_page': url_for('frontend.local_plan', planning_authority=pla.id, _external=True)}

    elif active_plan_id is not None:

        plan = LocalPlan.query.get(active_plan_id)
        for doc in documents:
            if PlanDocument.query.filter_by(url=doc).first() is None:
                document = PlanDocument(url=doc)
                plan.plan_documents.append(document)
                db.session.add(plan)
                db.session.commit()

        # TODO get the actual contents and store in s3
        resp = {'OK': 200, 'check_page': url_for('frontend.local_plan',
                                                 planning_authority=request.json['pla_id'],
                                                 _anchor=plan.local_plan,
                                                 _external=True)}
    else:
        resp = {'OK': 404}

    return jsonify(resp)


@frontend.route('/local-plans/check-url', methods=['POST'])
def check_url():

    # Maybe best do this on origin only? the reason is that the plan policy urls
    # are sort of unknown provenance. The LA website urls I got from LGA
    website_origin = request.json.get('active_page_origin')
    website_location = request.json.get('active_page_location')

    # handle documents differently
    if website_location.endswith(('.pdf')):
        document = PlanDocument.query.filter_by(url=website_location).first()
        print(document)
        resp = {'OK': 200, 'type': 'document', 'document': document.to_dict(), 'local_plan': document.local_plan.to_dict()}

    elif website_origin is not None:

        try:
            pla = PlanningAuthority.query.filter_by(website=website_origin).one()
            resp = {'OK': 200, 'planning_authority': pla.to_dict()}
        except Exception as e:
            print(e)
            resp = {'OK': 404}

    elif website_location is not None:
        try:
            pla = PlanningAuthority.query.filter_by(plan_policy_url=website_location).one()
            print("FOUND BASED ON PLANNING POLICY DOC")
            resp = {'OK': 200, 'planning_authority': pla.to_dict() }
        except Exception as e:
            print(e)
            resp = {'OK': 404}

    return jsonify(resp)


@frontend.route('/local-plans/check')
def lucky_dip():
    import random
    query = db.session.query(PlanningAuthority)
    row_count = int(query.count())
    pla = query.offset(int(row_count * random.random())).first()
    return render_template('lucky-dip.html', planning_authority=pla)


@frontend.route('/local-plans/<planning_authority>/check-plan-documents')
def check_documents(planning_authority):
    pla = PlanningAuthority.query.get(planning_authority)
    return render_template('check-plan-documents.html', planning_authority=pla)
