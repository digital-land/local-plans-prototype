import csv
import datetime
import os
from pathlib import Path

from dotenv import load_dotenv
from application.factory import create_app
from application.extensions import db
from application.models import LocalPlan, PlanningAuthority
from munger.munge import _get_org, _normalise_name


def format_short_date(date):
    if date is not None:
        return date.strftime('%b-%y')
    return date


def create_csv():
    plans = db.session.query(LocalPlan).all()
    dates_to_id = {}
    for p in plans:
        ds = [format_short_date(d) for d in [p.published_date, p.submitted_date, p.sound_date, p.adopted_date] if
              d is not None]
        if ds:
            for auth in p.planning_authorities:
                key = tuple(ds + [auth.name.lower().strip()])
                dates_to_id[key] = p
    output = []
    headers = []
    with open('./pins-local-plans-may-2019.csv', 'r') as f:
        csv_reader = csv.DictReader(f)
        for row in csv_reader:

            council = row['Local Council']
            org = _normalise_name(_get_org(council))

            candidate_key = []
            if row.get('Published'):
                candidate_key.append(row.get('Published'))
            if row.get('Submitted'):
                candidate_key.append(row.get('Submitted'))
            if row.get('Found Sound'):
                candidate_key.append(row.get('Found Sound'))
            if row.get('Adopted'):
                candidate_key.append(row.get('Adopted'))
            candidate_key.append(org.lower().strip())

            if candidate_key:
                k = tuple(candidate_key)
                if k in dates_to_id:
                    plan = dates_to_id[k]
                    for auth in plan.planning_authorities:
                        if org.lower().strip() == auth.name.lower().strip():
                            o = row
                            o['normalised_council_name'] = org
                            o['prototype_plan_id'] = plan.id
                            o['prototype_plan_title'] = plan.title
                            o['removed_from_prototype_csv'] = plan.deleted
                else:
                    o = row

                output.append(o)
    headers = ['prototype_plan_id', 'prototype_plan_title', 'normalised_council_name', 'removed_from_prototype_csv',
               'Local Council', 'Last Updated', 'Published', 'Submitted', 'Found Sound', 'Adopted']
    with open('./prototype-ids-to-pins-may-2019.csv', 'w') as f:
        csv_writer = csv.DictWriter(f, fieldnames=headers)
        csv_writer.writeheader()  # write header
        csv_writer.writerows(output)


date_fields = ['Published', 'Submitted', 'Found Sound', 'Adopted']

date_keys = {'Published': 'published_date',
             'Submitted': 'submitted_date',
             'Found Sound': 'sound_date',
             'Adopted': 'adopted_date'}

if __name__ == '__main__':

    dotenv_path = os.path.join(Path(os.path.dirname(__file__)).parent, '.flaskenv')
    load_dotenv(dotenv_path)

    app = create_app(os.getenv('FLASK_CONFIG') or 'config.DevelopmentConfig')
    with app.app_context():

        # create_csv()

        with open('./pins-local-plans-may-2019.csv', 'r') as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:

                council = row['Local Council'].strip()
                org = _normalise_name(_get_org(council))

                planning_auth = PlanningAuthority.query.filter_by(name=org).first()
                if planning_auth is not None:
                    for p in planning_auth.local_plans:
                        dates = [format_short_date(d) for d in
                                 [p.published_date, p.submitted_date, p.sound_date, p.adopted_date] if d is not None]
                        updated_dates = []
                        for f in date_fields:
                            if row.get(f):
                                updated_dates.append(row.get(f))

                        if dates and dates == updated_dates[:len(dates)]:
                            if len(updated_dates) > len(dates):
                                print('candidate for update', dates, '=>', updated_dates, p.title, p.id )
                                updates_to = date_fields[len(dates):len(updated_dates)]
                                print('to update', updates_to)
                                for d in updates_to:
                                    update = row[d]
                                    date_field_name = date_keys[d]
                                    update_date = datetime.datetime.strptime(update, '%b-%y').date()
                                    print('Set', date_field_name, 'to', update_date)
                                    setattr(p, date_field_name, update_date)
                                db.session.add(p)
                                db.session.commit()
                            else:
                                pass
                                # print('no updated needed', dates, '==', updated_dates )
                        else:
                            pass
                            # print('no match on dates', dates, '!=', updated_dates, p.title, p.id)
    print('Done')