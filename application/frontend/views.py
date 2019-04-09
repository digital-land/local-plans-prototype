import base64
import csv
import datetime
import io
import json
import uuid
from pathlib import Path
from urllib.parse import urlparse

import boto3
import sqlalchemy
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    send_file,
    current_app,
    make_response
)
from sqlalchemy import func, or_

from application.extensions import db, flask_optimize
from application.frontend.forms import LocalDevelopmentSchemeURLForm, LocalPlanURLForm, AddPlanForm, MakeJointPlanForm
from application.models import (
    PlanningAuthority,
    LocalPlan,
    FactType,
    EmergingFactType,
    PlanDocument,
    OtherDocument,
    Fact
)

from application.filters import format_fact

frontend = Blueprint('frontend', __name__, template_folder='templates')


@frontend.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@frontend.route('/planning-authority', methods=['GET', 'POST'])
def planning_authority_list():
    planning_authorities = PlanningAuthority.query.order_by(PlanningAuthority.name).all()
    if request.method == 'POST':
        print("Redirecting to ..........", request.form['local-authority-select'])
        return redirect(url_for('frontend.planning_authority', planning_authority=request.form['local-authority-select']))
    return render_template('planning-authority-list.html', planning_authorities=planning_authorities)


@frontend.route('/planning-authority/<planning_authority>')
def planning_authority(planning_authority):
    pla = PlanningAuthority.query.get(planning_authority)
    facts = pla.gather_facts()
    return render_template('planning-authority.html', planning_authority=pla, facts=facts)


@frontend.route('/local-plans', methods=['GET', 'POST'])
def list_all():
    planning_authorities = PlanningAuthority.query.order_by(PlanningAuthority.name).all()
    if request.method == 'POST':
        return redirect(url_for('frontend.local_plan', planning_authority=request.form['local-authority-select']))
    return render_template('local-plans.html', planning_authorities=planning_authorities)


@frontend.route('/local-plans/<planning_authority>', methods=['GET', 'POST'])
def local_plan(planning_authority):
    pla = PlanningAuthority.query.get(planning_authority)
    form = AddPlanForm(planning_authority=pla.code())
    if form.validate_on_submit():
        start_year = datetime.datetime(year=form.start_year.data, month=1, day=1)
        end_year = datetime.datetime(year=form.end_year.data, month=1, day=1)
        title = form.title.data
        plan = LocalPlan(title=title, start_year=start_year, plan_start_year=start_year, plan_end_year=end_year)
        plan.planning_authorities.append(pla)
        db.session.add(pla)
        db.session.commit()
        return redirect(url_for('frontend.local_plan', planning_authority=pla.id))

    elif request.method == 'POST':
        req_data = request.get_json()
        print(req_data)
        if 'original_title' in req_data and 'new_title' in req_data:
            #
            # TODO save the change to the plan title
            #
            resp = {"OK": 200, "original_title": req_data['original_title'], "new_title": req_data['new_title']}
        else:
            resp = {"OK": 204}
        return jsonify(resp)

    return render_template('local-plan.html',
                           planning_authority=pla,
                           fact_types=FactType,
                           emerging_fact_types=EmergingFactType,
                           form=form)

@frontend.route('/local-plans/<planning_authority>/<plan_id>/update-plan-period', methods=['POST'])
def update_plan_period(planning_authority, plan_id):
    plan = LocalPlan.query.get(plan_id)
    if plan is not None:
        start_year = int(request.json.get('start-year'))
        end_year = int(request.json.get('end-year'))
        plan.plan_start_year = datetime.datetime(start_year,1,1)
        plan.plan_end_year = datetime.datetime(end_year,1,1)
        plan.plan_period_found = True
        db.session.add(plan)
        db.session.commit()
        resp = {"OK": 200, "plan": plan.to_dict()}
    else:
        resp = {"OK": 204, "error": "Can't find that plan"}
    return jsonify(resp)


@frontend.route('/local-plans/<planning_authority>/<plan_id>/update-plan-housing-requirement', methods=['POST'])
def update_plan_housing_requirement(planning_authority, plan_id):
    plan = LocalPlan.query.get(plan_id)
    if plan is not None:
        data = {
            'housing_number_type': request.form['housing_number_type'],
            'housing_number_type_display': format_fact(request.form['housing_number_type']),
            'created_date': datetime.datetime.utcnow().isoformat(),
            'source_document': request.form['source_document'],
        }
        if 'range' in request.form['housing_number_type']:
            data['min'] = int(request.form['min'])
            data['max'] = int(request.form['max'])
        else:
            data['number'] = int(request.form['number'])

        bucket = 'local-plans'
        key = f'images/{plan.id}/{uuid.uuid4()}.jpg'
        s3 = boto3.client('s3')
        s3.upload_fileobj(request.files['screenshot'], bucket, key, ExtraArgs={'ContentType': 'image/jpeg', 'ACL': 'public-read'})
        data['image_url'] = f'https://s3.eu-west-2.amazonaws.com/{bucket}/{key}'
        plan.housing_numbers = data
        plan.housing_numbers_found = True
        db.session.add(plan)
        db.session.commit()
        resp = make_response(jsonify(data=data))
        resp.status_code = 200
        resp.headers = {'Content-Type': 'application/json'}
        return resp
    else:
        return make_response(jsonify({'error': 'could not find plan to update'}), 404)


@frontend.route('/local-plans/<planning_authority>/<plan_id>/update-plan-flags', methods=['POST'])
def update_plan_data_flags(planning_authority, plan_id):
    plan = LocalPlan.query.get(plan_id)

    # TODO plan has two fields, plan_period_found and housing_numbers_found which would at this stage
    # be null. You can set the appropriate flag to False and then save to db

    if plan is not None:
        if request.json.get('data-type') is not None:
            # user saying data can't be found
            found = False if bool(request.json.get('not-found')) else None

            if request.json.get('data-type') == 'housing-number':
                plan.housing_numbers_found = found
            else:
                plan.plan_period_found = found

            db.session.add(plan)
            db.session.commit()
            resp = {'OK': 200, 'plan': plan.to_dict(planning_authority) }
        else:
            resp = {'OK': 400, 'error': 'Data type not provided'}
    else:
        resp = {'OK': 400, 'error': 'Plan not found'}

    return jsonify(resp)

@frontend.route('/start-collecting-data')
def start_collecting_data():
    return render_template('collecting-data-start-page.html')


@frontend.route('/local-plans/<planning_authority>/document/<document>', methods=['POST'])
def add_fact_to_document(planning_authority, document):

    fact_json = request.json.get('fact')

    if fact_json is not None :
        document_type = fact_json.get('document_type')

        if document_type == 'plan_document':
            local_plan_id = request.args.get('local_plan')
            document = PlanDocument.query.filter_by(id=document, local_plan_id=local_plan_id).one()
        elif document_type == 'emerging_plan_document':
            document = OtherDocument.query.filter_by(id=document, planning_authority_id=planning_authority).one()

        fact = Fact(fact=fact_json.get('fact'), fact_type=fact_json.get('fact_type'), notes=fact_json.get('notes'))

        if 'RANGE' in fact_json.get('fact_type') or 'PERIOD' in fact_json.get('fact_type'):
            fact.from_, fact.to = fact_json.get('fact').split(',')

        document.facts.append(fact)
        db.session.add(document)
        db.session.commit()
        remove_url = url_for('frontend.remove_fact_from_document', document=str(document.id), fact=fact.id, document_type=document_type)
        resp = {'OK': 200, 'fact': fact.to_dict(), 'remove_url': remove_url}

        if fact_json.get('screenshot') is not None:
            data = fact_json['screenshot'].replace('data:image/jpeg;base64,', '')
            try:
                body = base64.b64decode(data)
                bucket = 'local-plans'
                key = f'images/{fact.id}.jpg'
                s3 = boto3.resource('s3')
                object = s3.Object(bucket, key)
                object.put(ACL='public-read', Body=body, ContentType='image/jpeg')
                image_url = f'https://s3.eu-west-2.amazonaws.com/{bucket}/{key}'
                fact.image_url = image_url
                db.session.add(fact)
                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                resp['error'] = 'Could not save image'
    else:
        resp = {'OK': 200}

    return jsonify(resp)


@frontend.route('/local-plans/<document>/<fact>', methods=['GET', 'DELETE'])
def remove_fact_from_document(document, fact):
    fact = Fact.query.filter_by(id=fact, document_id=document).first()
    if fact is not None:
        db.session.delete(fact)
        db.session.commit()
    return jsonify({204: 'No Content'})


@frontend.route('/local-plans/<planning_authority>/update-scheme-url', methods=['GET', 'POST'])
def update_local_scheme_url(planning_authority):
    pla = PlanningAuthority.query.get(planning_authority)
    form = LocalDevelopmentSchemeURLForm(url=pla.local_scheme_url)

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

    if request.method == 'POST' and request.json['policy-url'] is not None:
        plan.url = request.json['policy-url']
        db.session.add(pla)
        db.session.commit()
        resp = {'OK': 200, 'plan': plan.to_dict()}
        return jsonify(resp)
    else:
        form = LocalPlanURLForm(url=plan.url)
        if form.validate_on_submit():
            plan.url = form.url.data
            db.session.add(pla)
            db.session.commit()
            return redirect(url_for('frontend.local_plan', planning_authority=pla.id))

    return render_template('update-plan-url.html', planning_authority=pla, local_plan=plan, form=form)


@frontend.route('/local-plans/<planning_authority>/<local_plan>/update', methods=['POST'])
def update_plan(planning_authority, local_plan):

    plan_identifier = request.json['new_identifier'].strip()
    original_identifier = request.json['original_identifier'].strip()
    try:
        plan = LocalPlan.query.get(local_plan)
        plan.title = plan_identifier
        db.session.add(plan)
        db.session.commit()
        return jsonify({'message': 'plan identifier updated', 'OK': 200})
    except Exception as e:
        current_app.logger.exception(e)
        return jsonify({'error': 'Could not update plan',
                        'new_identifier': plan_identifier,
                        'original_identifier': original_identifier})


@frontend.route('/local-plans/<local_plan>/document/<document>', methods=['DELETE'])
def remove_document_from_plan(local_plan, document):
    doc = PlanDocument.query.filter_by(local_plan_id=local_plan, id=document).first()
    if doc is not None:
        db.session.delete(doc)
        db.session.commit()
    return jsonify({204: 'No Content'})


@frontend.route('/local-plans/planning-authority/<planning_authority>/document/<document>', methods=['DELETE'])
def remove_document_from_planning_authority(planning_authority, document):
    doc = OtherDocument.query.filter_by(planning_authority_id=planning_authority, id=document).first()
    if doc is not None:
        db.session.delete(doc)
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


# TODO can these two add_document_to_plan and add_document be merged?

@frontend.route('/local-plans/<planning_authority>/document', methods=['POST'])
def add_document_to_plan(planning_authority):

    document_type = request.args.get('document_type')

    if request.json.get('url') is not None:
        url = request.json['url']

        if document_type == 'plan_document':
            local_plan = request.args.get('local_plan')
            add_to = LocalPlan.query.get(local_plan)
            document = PlanDocument.query.filter_by(url=url, local_plan=add_to).first()
            if document is None:
                document = PlanDocument(url=url, title=request.json['doc_title'])
                add_to.plan_documents.append(document)
                db.session.add(add_to)
                db.session.commit()
            remove_url = url_for('frontend.remove_document_from_plan',
                                 document=str(document.id),
                                 local_plan=add_to.id)
            add_fact_url = url_for('frontend.add_fact_to_document',
                                   planning_authority=planning_authority,
                                   local_plan=add_to.id,
                                   document=str(document.id))

        elif document_type == 'emerging_plan_document':
            # TODO - update this to other_document
            add_to = PlanningAuthority.query.get(planning_authority)
            document = OtherDocument.query.filter_by(url=url, planning_authority=add_to).first()
            if document is None:
                if request.json.get('doc_title') is not None:
                    document = OtherDocument(url=url, title=request.json.get('doc_title'))
                else:
                    document = OtherDocument(url=url, title='Local Development Scheme')
                add_to.other_documents.append(document)
                db.session.add(add_to)
                db.session.commit()

            remove_url = url_for('frontend.remove_document_from_planning_authority',
                                 document=str(document.id),
                                 planning_authority=add_to.id)
            add_fact_url = url_for('frontend.add_fact_to_document',
                                   planning_authority=planning_authority,
                                   document=str(document.id))

        resp = {'OK': 200, 'url': url, 'document': document.to_dict(), 'remove_url': remove_url, 'add_fact_url': add_fact_url}
    else:
        resp = {'OK': 200}

    return jsonify(resp)


@frontend.route('/local-plans/add-document', methods=['POST'])
def add_document():
    documents = request.json['documents']
    active_plan_id = request.json.get('active_plan')
    website = (request.json.get('active_page_origin') if request.json.get('active_page_origin') is not None else _get_planning_authority_url(documents))

    if active_plan_id == 'localDevelopmentScheme' and website is not None:

        pla = PlanningAuthority.query.filter_by(website=website).one()
        for doc in documents:
            if OtherDocument.query.filter_by(url=doc).first() is None:
                pla.other_documents.append(OtherDocument(url=doc, title='Local Development Scheme'))

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


 # TODO is this only used from extension?
@frontend.route('/local-plans/planning-authority', methods=['POST'])
def planning_authority_from_document():

    # Maybe best do this on origin only? the reason is that the plan policy urls
    # are sort of unknown provenance. The LA website urls I got from LGA
    website_origin = request.json.get('active_page_origin')
    website_location = request.json.get('active_page_location')

    # handle documents differently
    if website_location.endswith(('.pdf')):
        # first check for Emerging Plan document
        if OtherDocument.query.filter_by(url=website_location).first() is not None:
            document = OtherDocument.query.filter_by(url=website_location).first()
            add_fact_url = url_for('frontend.add_fact_to_document',
                                   planning_authority=document.planning_authority_id,
                                   document=str(document.id),
                                   _external=True)
            resp = {'OK': 200, 'view-type': 'emerging-plan-document', 'document': document.to_dict(), 'add_fact_url': add_fact_url}
        elif PlanDocument.query.filter_by(url=website_location).first() is not None:

            document = PlanDocument.query.filter_by(url=website_location).first()
            add_fact_url = url_for('frontend.add_fact_to_document',
                                   planning_authority=document.local_plan.planning_authorities[0].id,
                                   local_plan=document.local_plan_id,
                                   document=str(document.id),
                                   _external=True)
            resp = {'OK': 200, 'view-type': 'plan-document', 'document': document.to_dict(), 'local_plan': document.local_plan.to_dict(), 'add_fact_url': add_fact_url}

        else:
            try:
                pla = PlanningAuthority.query.filter_by(website=website_origin).one()

                # TODO this is a new document, we could add item to response json to indicate to caller that
                # this can be added to local planning_authority or plan?

                resp = {'OK': 200, 'view-type': 'new-document', 'planning_authority': pla.to_dict(), 'document_url': website_location }
            except Exception as e:
                print(e)
                resp = {'OK': 404}

    elif website_origin is not None:

        try:
            origin = urlparse(website_origin)
            pla = PlanningAuthority.query.filter(PlanningAuthority.website.like(f'%{origin.netloc}%')).one()
            resp = {'OK': 200, 'view-type': 'urls', 'planning_authority': pla.to_dict()}
        except Exception as e:
            print(e)
            resp = {'OK': 404}

    elif website_location is not None:
        try:
            origin = urlparse(website_origin)
            pla = PlanningAuthority.query.filter_by(PlanningAuthority.plan_policy_url.like(f'%{origin.netloc}%')).one()
            resp = {'OK': 200, 'view-type': 'urls', 'planning_authority': pla.to_dict() }
        except Exception as e:
            print(e)
            resp = {'OK': 404}

    return jsonify(resp)


@frontend.route('/local-plans/lucky-dip')
def lucky_dip():
    import random
    query = db.session.query(LocalPlan).filter(or_(LocalPlan.plan_start_year.is_(None), LocalPlan.plan_end_year.is_(None)))
    row_count = int(query.count())
    local_plan = query.offset(int(row_count * random.random())).first()
    if local_plan is None:
        count_query = '''SELECT COUNT(*)
                         FROM local_plan l, document d, fact f 
                         WHERE l.id = d.local_plan_id
                         AND d.id = f.document_id
                         AND l.plan_start_year is not null
                         AND l.plan_end_year is not null
                         AND d.id not in (SELECT f.document_id FROM fact f WHERE f.fact_type ILIKE '%HOUSING%')
                         '''
        result = db.session.execute(sqlalchemy.text(count_query))

        count = result.next()[0]

        lp_query = f'''SELECT l.id FROM local_plan l, document d, fact f
                       WHERE l.id = d.local_plan_id
                       AND d.id = f.document_id
                       AND l.plan_start_year is not null
                       AND l.plan_end_year is not null
                       AND d.id not in (SELECT f.document_id FROM fact f WHERE f.fact_type ILIKE '%HOUSING%')
                       OFFSET floor(random()* {count}) LIMIT 1;'''

        q = sqlalchemy.text(lp_query)

        result = db.session.execute(q)
        plan_id = result.next()[0]
        local_plan = db.session.query(LocalPlan).filter(LocalPlan.id == plan_id).first()

    return render_template('lucky-dip.html', local_plan=local_plan, plan_id=str(local_plan.id))


@frontend.route('/local-plans/<planning_authority>/check-plan-documents')
def check_documents(planning_authority):
    pla = PlanningAuthority.query.get(planning_authority)
    return render_template('check-plan-documents.html', planning_authority=pla)


@frontend.route('/local-plans/chrome-extension')
def get_extension():
    import os
    import shutil
    path = Path(os.path.dirname(os.path.realpath(__file__)))
    base_path = path.parent.parent
    extension_dir = os.path.join(base_path, 'extensions', 'chrome')
    zip_path = shutil.make_archive('local-plan-extension', 'zip', extension_dir)
    return send_file(zip_path, attachment_filename='local-plan-extension.zip', as_attachment=True)


@frontend.route('/local-plans/data')
def data():
    planning_authorities = PlanningAuthority.query.all()
    data = []
    for pla in planning_authorities:
        for fact in pla.gather_facts(as_dict=True):
            data.append(fact)
    return render_template('data.html', data=data)


@frontend.route('/local-plans/data.json')
def data_as_json():
    planning_authorities = PlanningAuthority.query.all()
    data = []
    for pla in planning_authorities:
        data.append(pla.to_dict())
    return jsonify(data=data)


@frontend.route('/local-plans/data.csv')
def data_as_csv():
    planning_authorities = PlanningAuthority.query.all()
    data = []
    for pla in planning_authorities:
        for fact in pla.gather_facts(as_dict=True):
            fact.pop('id')
            fact.pop('document')
            fact.pop('fact_type_display')
            if fact.get('from') is not None and fact.get('to') is not None:
                fact.pop('fact')
            data.append(fact)

    fieldnames = ['planning_authority', 'plan', 'fact_type', 'fact', 'from', 'to', 'document_url', 'notes', 'created_date', 'screenshot']

    with io.StringIO() as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames, quoting=csv.QUOTE_ALL, lineterminator="\n")
        writer.writeheader()
        for row in data:
            writer.writerow(row)
        out = make_response(output.getvalue())

    out.headers["Content-Disposition"] = "attachment; filename=local-plan-data.csv"
    out.headers["Content-type"] = "text/csv"
    return out


@frontend.route('/local-plans/map-of-data')
@flask_optimize.optimize()
def map_of_data():
    data = []
    planning_authorities = db.session.query(PlanningAuthority,
                                            func.ST_AsGeoJSON(
                                                func.ST_SimplifyVW(PlanningAuthority.geometry, 0.00001)
                                            ).label('geojson')).all()
    for pla, geojson in planning_authorities:
        authority = {'planning_authority': pla.id,
                     'planning_authority_name': pla.name,
                     'plans': [],
                     'has_housing_numbers': False}
        for p in pla.local_plans:
            plan = {'plan_id': p.local_plan,
                    'status': p.latest_state().to_dict(),
                    'has_housing_numbers': p.has_housing_numbers()
                    }
            try:
                if p.has_housing_numbers():
                    authority['has_housing_numbers'] = True
                    if 'range'in p.housing_numbers['housing_number_type'].lower():
                        plan[f"{p.housing_numbers['housing_number_type']}_from".lower()] = p.housing_numbers['min']
                        plan[f"{p.housing_numbers['housing_number_type']}_to".lower()] = p.housing_numbers['max']
                    else:
                        plan[p.housing_numbers['housing_number_type'].lower()] = p.housing_numbers['number']
            except Exception as e:
                print(e)

            authority['plans'].append(plan)
        if geojson is not None:
            authority['geojson'] = json.loads(geojson)
        data.append(authority)
    return render_template('map-of-data.html', data=data)


@frontend.route('/local-plans/<planning_authority>/<local_plan>/make-joint-plan', methods=['GET', 'POST'])
def make_joint_plan(planning_authority, local_plan):
    planning_authority = PlanningAuthority.query.get(planning_authority)
    planning_authorities = PlanningAuthority.query.filter(PlanningAuthority.id != planning_authority.id).order_by(PlanningAuthority.name).all()
    plan = LocalPlan.query.get(local_plan)
    form = MakeJointPlanForm()
    form.planning_authorities.choices = [(p.id, p.name) for p in planning_authorities]
    if form.validate_on_submit():
        for id in form.planning_authorities.data:
            pla = PlanningAuthority.query.get(id)
            plan.planning_authorities.append(pla)
        db.session.add(plan)
        db.session.commit()
        return redirect(url_for('frontend.local_plan', planning_authority=planning_authority.id))

    return render_template('make-joint-plan.html', planning_authority=planning_authority, local_plan=plan, form=form)
