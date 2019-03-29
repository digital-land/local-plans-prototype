import csv
import json
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen

import boto3
import click
import ijson
import requests

from flask.cli import with_appcontext
from contextlib import closing
from application.extensions import db
from application.models import (
    PlanningAuthority,
    LocalPlan,
    PlanDocument,
    OtherDocument,
    Fact,
    HousingDeliveryTest,
    Document
)


json_to_geo_query = "SELECT ST_SetSRID(ST_GeomFromGeoJSON('%s'), 4326);"

def floaten(event):
    if event[1] == 'number':
        return (event[0], event[1], float(event[2]))
    else:
        return event

HDT_URL = 'https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/779711/HDT_2018_measurement.xlsx'


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

    db.session.query(HousingDeliveryTest).delete()
    db.session.commit()

    local_authorities = 'https://raw.githubusercontent.com/digital-land/alpha-data/master/local-authorities.csv'
    print('Loading', local_authorities)
    with closing(requests.get(local_authorities, stream=True)) as r:
        reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter=',')
        for row in reader:
            pa = PlanningAuthority.query.get(row['local-authority'])
            if pa is not None:
                pa.ons_code = row['ons-code'].strip()
                print('Set ons code for', pa.id)
                db.session.add(pa)
                db.session.commit()

    current_path = Path(os.path.abspath(__file__))
    hdt_file = os.path.join(current_path.parent.parent, 'housing-delivery-test.csv')
    with open(hdt_file, 'r') as f:
        reader = csv.DictReader(f, delimiter=',')
        print(reader.fieldnames)
        for row in reader:
            pla = PlanningAuthority.query.filter_by(ons_code=row['ons-code']).first()
            if pla is not None:
                homes_required = row['required-2015-16']
                homes_delivered = row['delivered-2015-16']
                from_year = datetime.strptime('2015', '%Y').date()
                to_year = datetime.strptime('2016', '%Y').date()

                hdt = HousingDeliveryTest.query.filter_by(from_year=from_year,
                                                          to_year=to_year,
                                                          homes_required=homes_required,
                                                          homes_delivered=homes_delivered,
                                                          planning_authority=pla).first()

                if hdt is None:
                    hdt = HousingDeliveryTest(from_year=from_year,
                                              to_year=to_year,
                                              homes_required=homes_required,
                                              homes_delivered=homes_delivered)

                    pla.housing_delivery_tests.append(hdt)
                    document = OtherDocument(url=HDT_URL, title='Housing Delivery Test: 2018 measurement')
                    print('Added hdt for years', hdt.from_year, hdt.from_year, 'to LA', pla.id)

                else:
                    print('hdt for', pla.id, 'for years', hdt.from_year, hdt.from_year, 'already added')

                homes_required = row['required-2016-17']
                homes_delivered = row['delivered-2016-17']
                from_year = datetime.strptime('2016', '%Y').date()
                to_year = datetime.strptime('2017', '%Y').date()

                hdt = HousingDeliveryTest.query.filter_by(from_year=from_year,
                                                          to_year=to_year,
                                                          homes_required=homes_required,
                                                          homes_delivered=homes_delivered,
                                                          planning_authority=pla).first()

                if hdt is None:
                    hdt = HousingDeliveryTest(from_year=from_year,
                                              to_year=to_year,
                                              homes_required=homes_required,
                                              homes_delivered=homes_delivered)

                    pla.housing_delivery_tests.append(hdt)
                    print('Added hdt for years', hdt.from_year, hdt.from_year, 'to LA', pla.id)
                else:
                    print('hdt for', pla.id, 'for years', hdt.from_year, hdt.from_year, 'already added')

                homes_required = row['required-2017-18']
                homes_delivered = row['delivered-2017-18']
                from_year = datetime.strptime('2017', '%Y').date()
                to_year = datetime.strptime('2018', '%Y').date()

                hdt = HousingDeliveryTest.query.filter_by(from_year=from_year,
                                                          to_year=to_year,
                                                          homes_required=homes_required,
                                                          homes_delivered=homes_delivered,
                                                          planning_authority=pla).first()

                if hdt is None:
                    hdt = HousingDeliveryTest(from_year=from_year,
                                              to_year=to_year,
                                              homes_required=homes_required,
                                              homes_delivered=homes_delivered)

                    pla.housing_delivery_tests.append(hdt)
                    print('Added hdt for years', hdt.from_year, hdt.from_year, 'to LA', pla.id)
                else:
                    print('hdt for', pla.id, 'for years', hdt.from_year, hdt.from_year, 'already added')

                pla.other_documents.append(document)
                db.session.add(pla)
                db.session.commit()


@click.command()
@with_appcontext
def load_geojson():

    from flask import current_app
    from application.extensions import db

    s3_region = current_app.config['S3_REGION']
    s3_bucket = current_app.config['S3_BUCKET']
    s3_bucket_url = 'http://%s.s3.amazonaws.com' % s3_bucket

    s3 = boto3.resource('s3', region_name=s3_region)

    planning_authority_feature_mappings = {}

    item_url = '%s/organisation.tsv' % s3_bucket_url
    print('Loading', item_url)
    with closing(requests.get(item_url, stream=True)) as r:
        reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter='\t')
        for row in reader:
            org = row['organisation']
            if 'local-authority' in org or 'national-park' in org:
                planning_authority = db.session.query(PlanningAuthority).get(org)
                if row.get('feature') is not None and planning_authority is not None:
                        planning_authority_feature_mappings[row.get('feature')] = planning_authority.id

    features_url = '%s/feature/local-authority-districts.geojson' % s3_bucket_url
    load_features(features_url, planning_authority_feature_mappings)

    features_url = '%s/feature/national-park-boundary.geojson' % s3_bucket_url
    load_features(features_url, planning_authority_feature_mappings)


def load_features(features_url, org_feature_mappings):

    print('Loading', features_url)

    try:
        if features_url.startswith('http'):
            f = urlopen(features_url)
        else:
            f = open(features_url, 'rb')
        events = map(floaten, ijson.parse(f))
        data = ijson.common.items(events, 'features.item')

        for feature in data:
            id = feature['properties'].get('feature')
            item = 'item:%s' % feature['properties'].get('item')
            feature_id = id if id is not None else item
            try:
                planning_authority = PlanningAuthority.query.get(org_feature_mappings[feature_id])
                geojson = json.dumps(feature['geometry'])
                planning_authority.geometry = db.session.execute(json_to_geo_query % geojson).fetchone()[0]
                db.session.add(planning_authority)
                db.session.commit()
            except KeyError as e:
                print('No organisation for feature', feature_id)
            except Exception as e:
                print(e)

    except Exception as e:
        print(e)
        print('Error loading', features_url)
    finally:
        try:
            f.close()
        except:
            pass


@click.command()
@with_appcontext
def clear():
    db.session.execute('DELETE FROM planning_authority_plan');
    db.session.query(HousingDeliveryTest).delete()
    db.session.query(Fact).delete()
    db.session.query(Document).delete()
    db.session.query(LocalPlan).delete()
    db.session.query(PlanningAuthority).delete()
    db.session.commit()

