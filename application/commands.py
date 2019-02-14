import csv
import click
import requests

from flask.cli import with_appcontext
from contextlib import closing
from application.extensions import db
from application.models import PlanningAuthority, LocalPlan, PlanDocument


def create_other_data(pa, row):
    plan_id = row['local-plan'].strip()
    plan = LocalPlan.query.get(plan_id)
    if plan is not None:
        status = [row['status'].strip(), row['date'].strip()]
        plan.states.append(status)
        print('updated local plan', plan_id)
    else:
        plan = LocalPlan()
        plan.local_plan = plan_id
        plan.planning_policy_url = row['plan-policy-url'].strip()
        plan.states = [[row['status'].strip(), row['date'].strip()]]
        pa.local_plans.append(plan)
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
                    db.session.add(pa)
                    db.session.commit()
                    print(row['organisation'], row['name'])
                else:
                    print(id, 'already in db')

                create_other_data(pa, row)


@click.command()
@with_appcontext
def clear():
    db.session.query(PlanDocument).delete()
    db.session.query(LocalPlan).delete()
    db.session.query(PlanningAuthority).delete()
    db.session.commit()

