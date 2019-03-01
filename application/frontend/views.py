from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from sqlalchemy import asc

from application.extensions import db
from application.models import PlanningAuthority, LocalPlan, PlanDocument, UncheckedDocument, Fact
from application.frontend.forms import PlanningPolicyURLForm

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
    return render_template('local-plans.html', planning_authority=pla)


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

    plan_document = PlanDocument.query.filter_by(id=document, local_plan=local_plan).one()

    if request.json.get('fact') is not None:
        fact = request.json['fact']
        fact = Fact(number=fact.get('number'), notes=fact.get('notes'))
        plan_document.facts.append(fact)
        db.session.add(plan_document)
        db.session.commit()
        remove_url = url_for('frontend.remove_fact_from_document', document=str(document.id), fact=fact.id)
        resp = {'OK': 200, 'fact': str(fact.id), 'remove_url': remove_url}
    else:
        resp = {'OK': 200}

    return jsonify(resp)


@frontend.route('/local-plans/<document>/<fact>', methods=['DELETE'])
def remove_fact_from_document(document, fact):
    # do something
    return jsonify({204: 'No Content'})


@frontend.route('/local-plans/<planning_authority>/update-planning-policy-url', methods=['GET', 'POST'])
def update_planning_policy_url(planning_authority):
    pla = PlanningAuthority.query.get(planning_authority)
    form = PlanningPolicyURLForm()

    if request.method == 'POST' and form.validate_on_submit():
        pla.plan_policy_url = form.url.data
        db.session.add(pla)
        db.session.commit()
        return redirect(url_for('frontend.local_plan', planning_authority=pla.id))

    # do I need to do this to populate the existing URL?
    if pla.plan_policy_url is not None and request.method == 'GET':
        form.url.data = pla.plan_policy_url

    return render_template('update-pp-url.html', planning_authority=pla, form=form)


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

    # Note this doesn't work as window.location.origin in chrome extensions isn't
    # location of parent window so for no get domain of local authority user is
    # on from documents
    # planning_authority = request.json['planning_authority']

    website = (request.json['active_page_origin']
        if request.json['active_page_origin'] is not "" else _get_planning_authority_url(documents))

    if website is not None:
        pla = PlanningAuthority.query.filter_by(website=website).one()
        for doc in documents:
            if UncheckedDocument.query.filter_by(url=doc).first() is None:
                pla.unchecked_documents.append(UncheckedDocument(url=doc))

        db.session.add(pla)
        db.session.commit()

        # TODO get the actual contents and store in s3
        resp = {'OK': 200, 'check_page': url_for('frontend.check_documents',
                                                 planning_authority=pla.id,
                                                 _external=True)}
    else:
        resp = {'OK': 200}

    return jsonify(resp)


# serialise planning authority as json obj
# should this be part of the model???
def make_planning_authority_obj(pla):
    obj = {
        'id': pla.id,
        'name': pla.name,
        'plans': []
    }
    print(obj)
    for plan in pla.local_plans:
        obj['plans'].append({
            'id': plan.local_plan,
            'title': plan.title
        })

    return obj


@frontend.route('/local-plans/check-url', methods=['POST'])
def check_url():
    website_origin = request.json['active_page_origin']
    website_location = request.json['active_page_location']

    if website_location is not "":
        pla = PlanningAuthority.query.filter_by(plan_policy_url=website_location).one()
        print("FOUND BASED ON PLANNING POLICY DOC")
        resp = {'OK': 200, 'planning_authority': make_planning_authority_obj(pla) }
    elif website_origin is not "":
        pla = PlanningAuthority.query.filter_by(website=website_origin).one()
        resp = {'OK': 200, 'planning_authority': make_planning_authority_obj(pla)}
    else:
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
