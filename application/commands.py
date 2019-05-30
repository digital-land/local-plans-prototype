import csv
import json
from urllib.request import urlopen

import boto3
import click
import ijson
import requests

from flask.cli import with_appcontext
from contextlib import closing

from application.models import (
    PlanningAuthority,
    LocalPlan
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
    local_authorities = 'https://raw.githubusercontent.com/communitiesuk/digital-land-data/master/data/organisation.tsv'
    print('Loading', local_authorities)
    with closing(requests.get(local_authorities, stream=True)) as r:
        reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter='\t')
        for row in reader:
            pa = PlanningAuthority.query.get(row['organisation'])
            if pa is not None:
                ons_code = row['area'].strip().split(':')[-1]
                print(ons_code)
                pa.ons_code = ons_code if ons_code else None
                db.session.add(pa)
                db.session.commit()

@click.command()
@with_appcontext
def load_geojson():

    from flask import current_app
    from application.extensions import db

    s3_region = current_app.config['S3_REGION']
    s3_bucket = 'digital-land-output'
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
    db.session.query(LocalPlan).delete()
    db.session.query(PlanningAuthority).delete()
    db.session.commit()


@click.command()
@with_appcontext
def cache_docs_in_s3():

    import tempfile
    import os
    from sqlalchemy.orm.attributes import flag_modified
    from application.extensions import db

    print('Cache plan documents in s3')

    s3 = boto3.client('s3')

    for plan in db.session.query(LocalPlan).all():
        if plan.housing_numbers is not None:
            if plan.housing_numbers.get('source_document') is not None:
                url = plan.housing_numbers.get('source_document')
                if url not in  [
                    'https://www.blackpool.gov.uk/Residents/Planning-environment-and-community/Documents/J118003-107575-2016-updated-17-Feb-2016-High-Res.pdf','http://staffsmoorlands-consult.objective.co.uk/file/4884627']:
                    try:
                        file = tempfile.NamedTemporaryFile(delete=False)
                        plan = process_file(file, plan, url, s3, existing_checksum=plan.housing_numbers.get('source_document_checksum'))
                        flag_modified(plan, 'housing_numbers')
                        db.session.add(plan)
                        db.session.commit()
                        print('Saved', plan.housing_numbers['cached_source_document'], 'with checksum',
                            plan.housing_numbers['source_document_checksum'])
                    except Exception as e:
                        print('error fetching', url)
                        print(e)
                    finally:
                        os.remove(file.name)


def hash_md5(file):
    import hashlib
    hash_md5 = hashlib.md5()
    with open(file, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_md5.update(chunk)
    return hash_md5


def process_file(file, plan, url, s3, existing_checksum=None):
    from flask import current_app
    import requests
    import shutil
    import base64

    try:
        print('Fetching', url, 'to', file.name)
        r = requests.get(url, stream=True)
        r.raise_for_status()
        content_type = r.headers['content-type']
        if content_type not in ['application/pdf', 'binary/octet-stream']:
            raise Exception('Probably not a pdf')
        shutil.copyfileobj(r.raw, file)
        file.flush()
        file.close()

        print('Download done')
        checksum = hash_md5(file.name)
        print('checksum', checksum.hexdigest())
        bucket = current_app.config['S3_BUCKET']
        key = f'plan-documents/{plan.id}.pdf'
        encoded_checksum = base64.b64encode(checksum.digest())

        upload_exists = True if existing_checksum is not None and existing_checksum == checksum.hexdigest() else False

        if not upload_exists:
            with open(file.name, 'rb') as f:
                resp = s3.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=f,
                    ACL='public-read',
                    ContentMD5=encoded_checksum.decode('utf-8'),
                    ContentType=content_type
                )
            print('Upload done')
            s3_url = f'https://s3.eu-west-2.amazonaws.com/{bucket}/{key}'
            plan.housing_numbers['cached_source_document'] = s3_url
            plan.housing_numbers['source_document_checksum'] = checksum.hexdigest()
            return plan

    except Exception as e:
        print(e)
