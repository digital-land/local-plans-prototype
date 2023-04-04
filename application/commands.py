import csv
import os
import datetime
import boto3
import click
import sqlalchemy

from sqlalchemy.orm.attributes import flag_modified
from pathlib import Path
from flask.cli import with_appcontext

from application.extensions import db

from application.models import PlanningAuthority, LocalPlan


date_fields = ["Published", "Submitted", "Found Sound", "Adopted"]

date_keys = {
    "Published": "published_date",
    "Submitted": "submitted_date",
    "Found Sound": "sound_date",
    "Adopted": "adopted_date",
}


@click.command()
@with_appcontext
def cache_docs_in_s3():

    import tempfile
    import os
    from application.extensions import db

    print("Cache plan documents in s3")

    s3 = boto3.client("s3")

    for i, plan in enumerate(
        db.session.query(LocalPlan).filter(LocalPlan.deleted.is_(False)).all()
    ):
        if plan.housing_numbers is not None:
            if plan.housing_numbers.get("source_document") is not None:
                url = plan.housing_numbers.get("source_document")
                try:
                    file = tempfile.NamedTemporaryFile(delete=False)
                    plan = process_file(
                        file,
                        plan,
                        url,
                        s3,
                        existing_checksum=plan.housing_numbers.get(
                            "source_document_checksum"
                        ),
                    )
                    print(f"Processed {url}")
                except Exception as e:
                    print(f"Error fetching {url}")
                    print(e)
                finally:
                    flag_modified(plan, "housing_numbers")
                    db.session.add(plan)
                    db.session.commit()
                    os.remove(file.name)
    print(f"Processed {i} plan documents")


@click.command()
@click.option("--pinscsv")
@with_appcontext
def pins_update(pinscsv):
    parent_dir = Path(os.path.dirname(__file__)).parent
    pins_csv = f"{parent_dir}/data/{pinscsv}"
    print("Loading data from", pins_csv)

    updates = []
    no_matches = []
    no_updates = []
    not_found = []
    errors = []

    with open(pins_csv, "r") as f:
        csv_reader = csv.DictReader(f)
        for row in csv_reader:
            try:
                council = row["Local Council"].strip()
                org = _normalise_name(_get_org(council))
                ons_code = row["LPA ONS Code"]
                planning_auth = PlanningAuthority.query.filter_by(
                    ons_code=ons_code
                ).one()
                row_matched = False

                for p in planning_auth.local_plans:
                    dates = [
                        d
                        for d in [
                            p.published_date,
                            p.submitted_date,
                            p.sound_date,
                            p.adopted_date,
                        ]
                        if d is not None
                    ]
                    updated_dates = []
                    for f in date_fields:
                        if row.get(f):
                            updated_dates.append(parse_date(row.get(f)))

                    if dates and dates == updated_dates[: len(dates)]:
                        row_matched = True

                        if len(updated_dates) > len(dates):
                            updates_to = date_fields[len(dates) : len(updated_dates)]
                            for field in updates_to:
                                update = row[field]
                                date_field_name = date_keys[field]
                                update_date = datetime.datetime.strptime(
                                    update, "%Y-%m-%d"
                                ).date()
                                setattr(p, date_field_name, update_date)
                                db.session.add(p)
                                db.session.commit()
                                updates.append(
                                    f"{p.id}, {p.title} set {date_field_name} to {update_date.strftime('%Y-%m-%d')}"
                                )
                        else:
                            formatted_dates = [d.strftime("%Y-%m-%d") for d in dates]
                            formatted_updated_dates = [
                                d.strftime("%Y-%m-%d") for d in updated_dates
                            ]
                            no_updates.append(
                                f"{p.id}, {p.title} {formatted_dates} matches {formatted_updated_dates}"
                            )

                if not row_matched:
                    formatted_updated_dates = [
                        d.strftime("%Y-%m-%d") for d in updated_dates
                    ]
                    no_matches.append(
                        f"Could not find a plan for {org}:{ons_code} matching any of these dates {formatted_updated_dates}"
                    )

            except sqlalchemy.orm.exc.NoResultFound as e:
                not_found.append(
                    f"No planning authority found for ons code {ons_code} normalised name -> {org}"
                )
            except Exception as e:
                errors.append(f"Error loading {row} - {e}")

    print(f"Report from loading {pinscsv}")
    print("=" * 80)
    if errors:
        print("Errors loading the following rows")
        print("=" * 80)
        for item in errors:
            print(item)
    if not_found:
        print("The following planning authorities were not found")
        print("=" * 80)
        for item in not_found:
            print(item)
    if no_matches:
        print("=" * 80)
        print("Rows in the pins csv that did not match any of our records")
        print("=" * 80)
        for item in no_matches:
            print(item)
    if no_updates:
        print("=" * 80)
        print(
            "The following rows in pins csv matched our current records and did not need updating"
        )
        print("=" * 80)
        for item in no_updates:
            print(item)
    if updates:
        print("=" * 80)
        print("The following rows in pins csv were updated in the prototype db")
        print("=" * 80)
        for item in updates:
            print(item)


def hash_md5(file):
    import hashlib

    hash_md5 = hashlib.md5()
    with open(file, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5


def process_file(file, plan, url, s3, existing_checksum=None):
    from flask import current_app
    import requests
    import shutil
    import base64

    try:
        print("Fetching", url, "to", file.name)
        # Add user agent header as it seems many of the sites block 'non browser' user agents
        r = requests.get(url, stream=True, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        content_type = r.headers["content-type"]
        if content_type not in ["application/pdf", "binary/octet-stream"]:
            plan.housing_numbers[
                "error_caching_source_document"
            ] = f"Document at {url} might not be a pdf"
            return plan
        shutil.copyfileobj(r.raw, file)
        file.flush()
        file.close()

        print("Download done")
        checksum = hash_md5(file.name)
        print("checksum", checksum.hexdigest())
        bucket = current_app.config["S3_BUCKET"]
        key = f"plan-documents/{plan.id}.pdf"
        encoded_checksum = base64.b64encode(checksum.digest())

        upload_exists = (
            True
            if existing_checksum is not None
            and existing_checksum == checksum.hexdigest()
            else False
        )

        if not upload_exists:
            with open(file.name, "rb") as f:
                resp = s3.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=f,
                    ACL="public-read",
                    ContentMD5=encoded_checksum.decode("utf-8"),
                    ContentType=content_type,
                )
            print("Upload done")
            s3_url = f"https://s3.eu-west-2.amazonaws.com/{bucket}/{key}"
            plan.housing_numbers["cached_source_document"] = s3_url
            plan.housing_numbers["source_document_checksum"] = checksum.hexdigest()

        return plan

    except Exception as e:
        print(e)
        plan.housing_numbers["error_caching_source_document"] = str(e)

    return plan


@click.command()
@click.option("--csvfile")
@with_appcontext
def load_ldf_csv(csvfile):

    parent_dir = Path(os.path.dirname(__file__)).parent
    ldfcsv = f"{parent_dir}/data/{csvfile}"
    print("Loading data from", ldfcsv)

    with open(ldfcsv, "r") as f:
        csv_reader = csv.DictReader(f)
        for row in csv_reader:
            try:
                plan_id = row["plan_id"]
                plan = LocalPlan.query.get(plan_id)
                ldf_number = int(row["local_development_framework_number"])
                if plan is not None:
                    plan.local_development_framework_number = ldf_number
                    db.session.add(plan)
                    db.session.commit()
                    print(f"Set ldf number {ldf_number} for plan {plan_id}")
            except Exception as e:
                print(e)
                print(f"Could not set ldf number for plan id {plan_id}")

    print("Done")


def _get_org(org):
    org = org.replace(" - Local plan Review", "")
    org = org.replace(" (inc South Downs NPA)", "")
    org = org.replace(" - first review", "")
    org = org.replace(" - Local Plan review", "")
    org = org.replace(" - Local Plan", "")
    org = org.replace(" (Review)", "")
    org = org.replace(" - New Southwark Plan", "")
    org = org.replace(" (Partial review)", "")
    org = org.replace(" (Local Plan 2015-2030)", "")
    org = org.replace(" (Revision)", "")
    org = org.replace(" Local Plan part 1 Review", "")
    org = org.replace(" - CS Review/Local Plan", "")
    org = org.replace(" - Strategic Policies Partial Review", "")
    org = org.replace(" - First review", "")
    org = org.replace(" 2014-2032", "")
    org = org.replace(" - Core Strategy Review", "")
    org = org.replace(" - Core Strategy Single Issue Review", "")
    org = org.replace(" 2033", "")
    org = org.replace(", Alterations to Strategic Policies", "")
    org = org.replace(" - Development Framework", "")
    org = org.replace(" - Core Strategy & Policies", "")
    org = org.replace(" - First review", "")
    org = org.replace(", Local Plan 2015", "")
    org = org.replace(" - Strategic Policies & Land Allocation", "")
    org = org.replace(" Selective Review", "")
    org = org.replace(" - Fast Track Single Policy Review", "")
    org = org.replace(" (review)", "")
    org = org.replace(" Focussed Review", "")
    org = org.replace(" - Housing Local Plan", "")
    org = org.replace(" Core Strategy Review", "")
    org = org.replace(" (Local Plan Review)", "")
    org = org.replace(" - Core Strategy re-opened", "")
    org = org.replace(" (New Local Plan)", "")
    org = org.replace(" - Consequential changes", "")
    org = org.replace(" (Plan:MK)", "")
    org = org.replace(" Review", "")

    return org.strip()


def _normalise_name(org):
    org = org.replace("DC", "District Council")
    org = org.replace("BC", "Borough Council")
    org = org.replace("Upon", "upon")
    if ", City of" in org:
        name = org.split(",")[0]
        org = f"City of {name}"
    if ", Royal Borough of" in org:
        name = org.split(",")[0]
        org = f"Royal Borough of {name}"
    if ", London Borough of" in org:
        name = org.split(",")[0]
        org = f"London Borough of {name}"
    if ", Borough of" in org:
        name = org.split(",")[0]
        org = f"Borough of {name}"

    return org.strip()


def parse_date(date):
    if date is not None and isinstance(date, str):
        return datetime.datetime.strptime(date, "%Y-%m-%d").date()
    return date
