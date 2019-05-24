#! /usr/bin/env python

import csv
from contextlib import closing
from datetime import datetime

import requests


joint_plan_map = {'West of England JSP': ['Bath and North East Somerset Council', 'Bristol City Council', 'North Somerset Council', 'South Gloucestershire Council'],
                  'South East Lincs Local Plan': ['Boston Borough Council', 'South Holland District Council'],
                  'Joint North Essex Local Plan part 1': ['Braintree District Council', 'Colchester Borough Council', 'Tendring District Council'],
                  'Plymouth & South West Devon Plan': ['Plymouth City Council', 'South Hams District Council', 'West Devon Borough Council']}


def _get_org_mapping():
    organisation_mapping = {}
    organisations = 'https://raw.githubusercontent.com/communitiesuk/digital-land-collector/master/data/organisation.tsv'

    print('Loading', organisations)
    with closing(requests.get(organisations, stream=True)) as r:
        reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter='\t')
        for row in reader:
            organisation_mapping[row['name'].strip()] = row['organisation'].strip()

    return organisation_mapping



def _transform_date(date_str):
    try:
        date = datetime.strptime(date_str, '%b-%y')
        return date.date().isoformat()
    except:
        return None


def _get_org(org):
    org = org.replace(' - Local plan Review', '')
    org = org.replace(' (inc South Downs NPA)', '')
    org = org.replace(' - first review', '')
    org = org.replace(' - Local Plan review', '')
    org = org.replace(' - Local Plan', '')
    org = org.replace(' (Review)', '')
    org = org.replace(' - New Southwark Plan', '')
    org = org.replace(' (Partial review)', '')
    org = org.replace(' (Local Plan 2015-2030)', '')
    org = org.replace(' (Revision)', '')
    org = org.replace(' Local Plan part 1 Review', '')
    org = org.replace(' - CS Review/Local Plan', '')
    org = org.replace(' - Strategic Policies Partial Review', '')
    org = org.replace(' - First review', '')
    org = org.replace(' 2014-2032', '')
    org = org.replace(' - Core Strategy Review', '')
    org = org.replace(' - Core Strategy Single Issue Review', '')
    org = org.replace(' 2033', '')
    org = org.replace(', Alterations to Strategic Policies', '')
    org = org.replace(' - Development Framework', '')
    org = org.replace(' - Core Strategy & Policies', '')
    org = org.replace(' - First review', '')
    org = org.replace(', Local Plan 2015', '')
    org = org.replace(' - Strategic Policies & Land Allocation', '')
    org = org.replace(' Selective Review', '')
    org = org.replace(' - Fast Track Single Policy Review', '')
    org = org.replace(' (review)', '')
    org = org.replace(' Focussed Review', '')
    org = org.replace(' - Housing Local Plan', '')
    org = org.replace(' Core Strategy Review', '')
    org = org.replace(' (Local Plan Review)', '')
    org = org.replace(' - Core Strategy re-opened', '')
    org = org.replace(' (New Local Plan)', '')
    org = org.replace(' - Consequential changes', '')
    org = org.replace(' (Plan:MK)', '')
    org = org.replace(' Review', '')

    return org.strip()


def _normalise_name(org):
    org = org.replace('DC', 'District Council')
    org = org.replace('BC', 'Borough Council')
    org = org.replace('Upon', 'upon')
    if ', City of' in org:
        name = org.split(',')[0]
        org = f'City of {name}'
    if ', Royal Borough of' in org:
        name = org.split(',')[0]
        org = f'Royal Borough of {name}'
    if ', London Borough of' in org:
        name = org.split(',')[0]
        org = f'London Borough of {name}'
    if ', Borough of' in org:
        name = org.split(',')[0]
        org = f'Borough of {name}'
    return org.strip()


def _get_year(date):
    if date is not None:
        return datetime.strptime(date, '%Y-%m-%d').year
    return None


def _get_subtitle(council):
    if ' - ' in council:
        sub = council.split(' - ')[-1].strip()
        if sub.lower() != 'local plan':
            return sub
    if ' (' in council:
        sub = council.split(' (')[-1].replace(')', '').strip()
        if sub.lower() != 'local plan':
            sub = sub.replace('inc ', 'including ')
            return sub
    if ' Focussed' in council:
        sub = council.split(' Focussed')[-1].strip()
        return f'Focussed {sub}'
    if ' Selective' in council:
        sub = council.split(' Selective')[-1].strip()
        return f'Selective {sub}'
    if ' Core' in council:
        sub = council.split(' Core')[-1].strip()
        return f'Core {sub}'
    if ', Alterations' in council:
        sub = council.split(', Alterations')[-1].strip()
        return f'Alterations {sub}'
    return None


def _handle_joint_plan(council):
    joint_plans = ['South East Lincs Local Plan',
                   'Plymouth & South West Devon Plan',
                   'West of England JSP',
                   'Joint North Essex Local Plan part 1']
    for p in joint_plans:
        if p in council:
            c = council.replace(p, '').replace('(', '').replace(')', '').replace(',', '').strip()
            return (_normalise_name(c), p)
    return None


def _get_combined_ids(plan_name):
    ids = []
    for o in joint_plan_map[plan_name]:
        ids.append(organisation_mapping.get(o))
    return '-'.join(sorted([id.split(':')[-1] for id in ids if id is not None]))


if __name__ == '__main__':

    organisation_mapping = _get_org_mapping()

    plans = {}

    with open('list-of-local-plans-data-science-team.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            plans[row['organisation']] = {'name': row['name'],
                                          'plan-url': row['plan-url'],
                                          'document-url': row['document-url'],
                                          'adopted-date': row['adopted-date']}



    date_keys = {'Last Updated': 'updated',
                 'Published': 'published',
                 'Submitted': 'submitted',
                 'Found Sound': 'sound',
                 'Adopted': 'adopted'}

    with open('pins-local-plans-feb-2019.csv') as f:
        reader = csv.DictReader(f)

        with open('local-plan-register.csv', 'w') as outfile:

            fieldnames = ['local-plan',
                          'title',
                          'organisation',
                          'name',
                          'plan-policy-url',
                          'status',
                          'plan-document-url',
                          'date',
                          'entry-date']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=',', lineterminator='\n', quoting=csv.QUOTE_ALL)
            writer.writeheader()
            today = datetime.now().date().isoformat()

            for row in reader:

                council = row['Local Council']

                joint_plan_authority = None
                joint_plan_authority = _handle_joint_plan(council)

                if joint_plan_authority is not None:
                    print(council, ' => ', joint_plan_authority)
                    org, title = joint_plan_authority
                else:
                    org = _normalise_name(_get_org(council))
                    title = _get_subtitle(council)

                org_code = organisation_mapping.get(org)

                plan = plans.get(org_code)


                for d in date_keys.keys():
                    if row.get(d):

                        formatted_date = _transform_date(row[d])
                        status = date_keys[d]

                        plan_url = plan.get('plan-url') if plan is not None else None
                        document_url = plan.get('document-url') if (plan is not None and status == 'adopted') else None

                        publication_year = _get_year(_transform_date(row['Published']))
                        if (org_code is not None or joint_plan_authority is not None) and formatted_date is not None and publication_year is not None:

                            if joint_plan_authority is not None:
                                plan_id = _get_combined_ids(joint_plan_authority[1])
                                local_plan = f'{plan_id}-{publication_year}'
                            else:
                                plan_id = org_code.split(':')[-1]
                                local_plan = f'{plan_id}-{publication_year}'

                            writer.writerow({'local-plan': local_plan,
                                             'title': title,
                                             'organisation': org_code,
                                             'name': org,
                                             'plan-policy-url': plan_url,
                                             'status': date_keys[d],
                                             'plan-document-url': document_url,
                                             'date': formatted_date,
                                             'entry-date': today})

