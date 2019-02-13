import csv
from contextlib import closing

import click
import requests
from flask.cli import with_appcontext

from application.extensions import db
from application.models import PlanningAuthority, LocalPlan, PlanDocument


def create_other_data(pa, row):

    plan = row['local-plan'].strip()
    if 'None' not in plan:
        status = row['status'].strip()
        planning_policy_url = row['plan-policy-url'].strip()
        date = row['date'].strip()
        entry_id = row['entry-number'].strip()

        lp = LocalPlan()
        lp.local_plan = plan
        lp.status = status
        lp.planning_policy_url = planning_policy_url
        if date:
            lp.date = date
        lp.entry_id = entry_id

        pa.local_plans.append(lp)
        db.session.add(pa)
        db.session.commit()
        print('loaded local plan', plan)

        if status == 'adopted' and row.get('plan-document-url') and row.get('plan-document-url') != '?':
            pd = PlanDocument(url=row.get('plan-document-url'))
            lp.plan_documents.append(pd)
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

