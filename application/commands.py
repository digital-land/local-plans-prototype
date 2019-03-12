import csv
from datetime import datetime
from pathlib import Path

import click
import requests

from flask.cli import with_appcontext
from contextlib import closing
from application.extensions import db
from application.models import PlanningAuthority, LocalPlan, PlanDocument, EmergingPlanDocument, Fact, EmergingFact, \
    HousingDeliveryTest


def create_other_data(pa, row):
    plan_id = row['local-plan'].strip()
    plan = LocalPlan.query.get(plan_id)
    if plan is not None:
        status = [row['status'].strip(), row['date'].strip()]
        if status not in plan.states:
            plan.states.append(status)
            print('updated local plan', plan_id)
        if pa not in plan.planning_authorities:
            pa.local_plans.append(plan)
    else:
        plan = LocalPlan()
        plan.local_plan = plan_id
        plan.url = row['plan-policy-url'].strip()
        plan.states = [[row['status'].strip(), row['date'].strip()]]
        pa.local_plans.append(plan)
        plan.title = row['title'].strip()
        print('created local plan', plan_id)

    db.session.add(pa)
    db.session.commit()
    print('loaded local plan', plan_id)

    if row['status'].strip() == 'adopted' and row.get('plan-document-url') and row.get('plan-document-url') != '?':
        pd = PlanDocument(url=row.get('plan-document-url'))
        plan.plan_documents.append(pd)
        db.session.add(pa)
        db.session.commit()
        print('loaded plan document for plan', plan, 'document', row.get('plan-document-url'))


@click.command()
@with_appcontext
def load():
    local_authorities = 'https://raw.githubusercontent.com/digital-land/alpha-data/master/local-authorities.csv'
    mapping = {}
    print('Loading', local_authorities)
    with closing(requests.get(local_authorities, stream=True)) as r:
        reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter=',')
        for row in reader:
            mapping[row['local-authority'].strip()] = row['website'].strip()

    register = 'https://raw.githubusercontent.com/digital-land/alpha-data/master/local-plans/local-plan-register.csv'
    print('Loading', register)
    with closing(requests.get(register, stream=True)) as r:
        reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter=',')
        for row in reader:
            id = row['organisation'].strip()
            name = row['name'].strip()
            if id != '':
                pa = PlanningAuthority.query.get(id)
                if pa is None:
                    pa = PlanningAuthority(id=id, name=name)
                    if mapping.get(id) is not None:
                        pa.website = mapping.get(id)
                    db.session.add(pa)
                    db.session.commit()
                    print(row['organisation'], row['name'])
                else:
                    print(id, 'already in db')

                create_other_data(pa, row)


@click.command()
@with_appcontext
def set_ons_codes():
    local_authorities = 'https://raw.githubusercontent.com/digital-land/alpha-data/master/local-authorities.csv'
    print('Loading', local_authorities)
    with closing(requests.get(local_authorities, stream=True)) as r:
        reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter=',')
        for row in reader:
            pa = PlanningAuthority.query.get(row['local-authority'])
            if pa is not None:
                pa.ons_code = row['ons-code'].strip()
                db.session.add(pa)
                db.session.commit()


@click.command()
@with_appcontext
def load_hdt():
    import os
    current_path = Path(os.path.abspath(__file__))
    hdt_file = os.path.join(current_path.parent.parent, 'housing-delivery-test.csv')
    with open(hdt_file, 'r') as f:
        reader = csv.DictReader(f, delimiter=',')
        print(reader.fieldnames)
        for row in reader:
            pla = PlanningAuthority.query.filter_by(ons_code=row['ons-code']).first()
            if pla is not None:
                hdt = HousingDeliveryTest()
                hdt.homes_required = row['required-2015-16']
                hdt.homes_delivered = row['delivered-2015-16']
                hdt.from_year = datetime.strptime('2015', '%Y').date()
                hdt.to_year = datetime.strptime('2016', '%Y').date()
                pla.housing_delivery_tests.append(hdt)
                db.session.add(pla)
                db.session.commit()

                hdt = HousingDeliveryTest()
                hdt.homes_required = row['required-2016-17']
                hdt.homes_delivered = row['delivered-2016-17']
                hdt.from_year = datetime.strptime('2016', '%Y').date()
                hdt.to_year = datetime.strptime('2017', '%Y').date()
                pla.housing_delivery_tests.append(hdt)
                db.session.add(pla)
                db.session.commit()

                hdt = HousingDeliveryTest()
                hdt.homes_required = row['required-2017-18']
                hdt.homes_delivered = row['delivered-2017-18']
                hdt.from_year = datetime.strptime('2017', '%Y').date()
                hdt.to_year = datetime.strptime('2018', '%Y').date()
                pla.housing_delivery_tests.append(hdt)
                db.session.add(pla)
                db.session.commit()



@click.command()
@with_appcontext
def clear():
    db.session.execute('DELETE FROM planning_authority_plan');
    db.session.query(Fact).delete()
    db.session.query(EmergingFact).delete()
    db.session.query(EmergingPlanDocument).delete()
    db.session.query(PlanDocument).delete()
    db.session.query(LocalPlan).delete()
    db.session.query(PlanningAuthority).delete()
    db.session.commit()

