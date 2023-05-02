import csv
import datetime
import io
import uuid
import boto3

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    current_app,
    make_response,
    flash,
    abort,
)

from markupsafe import Markup
from sqlalchemy.orm.attributes import flag_modified

from application.auth.utils import requires_auth, get_current_user
from application.extensions import db
from application.filters import format_housing_number_type
from application.frontend.forms import LocalPlanURLForm, AddPlanForm, MakeJointPlanForm

from application.models import PlanningAuthority, LocalPlan, HousingNumberType

frontend = Blueprint("frontend", __name__, template_folder="templates")


@frontend.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html", current_user=get_current_user())


@frontend.route("/local-plans", methods=["GET", "POST"])
def list_all():
    planning_authorities = PlanningAuthority.query.order_by(
        PlanningAuthority.name
    ).all()
    if request.method == "POST":
        return redirect(
            url_for(
                "frontend.local_plan",
                planning_authority=request.form["local-authority-select"],
            )
        )
    return render_template(
        "local-plans.html",
        planning_authorities=planning_authorities,
        current_user=get_current_user(),
    )


@frontend.route("/local-plans/<planning_authority>", methods=["GET", "POST"])
def local_plan(planning_authority):
    if planning_authority.startswith("government-organisation:"):
        govt_org = planning_authority.split(":")[1]
        pla = PlanningAuthority.query.filter(
            PlanningAuthority.government_organisation == govt_org
        ).one_or_none()
        if pla is not None and pla.id != planning_authority:
            return redirect(url_for("frontend.local_plan", planning_authority=pla.id))
    else:
        pla = PlanningAuthority.query.get(planning_authority)
    if pla is None:
        abort(404)
    form = AddPlanForm(planning_authority=pla.code())
    if form.validate_on_submit():
        start_year = datetime.datetime(year=form.start_year.data, month=1, day=1)
        end_year = datetime.datetime(year=form.end_year.data, month=1, day=1)
        title = form.title.data
        plan = LocalPlan(
            title=title, plan_start_year=start_year, plan_end_year=end_year
        )
        plan.planning_authorities.append(pla)
        plan.local_development_framework_number = (
            form.local_development_framework_number.data
        )
        db.session.add(pla)
        db.session.commit()
        return redirect(url_for("frontend.local_plan", planning_authority=pla.id))

    return render_template(
        "local-plan.html",
        planning_authority=pla,
        housing_number_types=HousingNumberType,
        form=form,
        current_user=get_current_user(),
    )


@frontend.route(
    "/local-plans/<planning_authority>/<plan_id>/update-plan-period", methods=["POST"]
)
@requires_auth
def update_plan_period(planning_authority, plan_id):

    plan = LocalPlan.query.get(plan_id)
    pla = PlanningAuthority.query.get(planning_authority)

    if plan is not None:
        if request.json.get("start-year"):
            start_year = int(request.json.get("start-year"))
            try:
                plan.plan_start_year = datetime.datetime(start_year, 1, 1)
            except ValueError as e:
                current_app.logger.exception(e)
                return jsonify(
                    {
                        "BAD REQUEST": 400,
                        "error": f"{plan.plan_start_year} not a valid year",
                    }
                )
        else:
            plan.plan_start_year = None

        if request.json.get("end-year"):
            end_year = int(request.json.get("end-year"))
            try:
                plan.plan_end_year = datetime.datetime(end_year, 1, 1)
            except ValueError as e:
                current_app.logger.exception(e)
                return jsonify(
                    {
                        "BAD REQUEST": 400,
                        "error": f"{plan.plan_end_year} not a valid year",
                    }
                )
        else:
            plan.plan_end_year = None

        if plan.plan_start_year is not None and plan.plan_end_year is not None:
            plan.plan_period_found = True

        db.session.add(plan)
        db.session.commit()

        resp = {"OK": 200, "plan": plan.to_dict(pla.id)}

    else:
        resp = {"OK": 404, "error": "Can't find that plan"}

    return jsonify(resp)


@frontend.route(
    "/local-plans/<planning_authority>/<plan_id>/update-plan-housing-requirement",
    methods=["POST"],
)
@requires_auth
def update_plan_housing_requirement(planning_authority, plan_id):
    plan = LocalPlan.query.get(plan_id)
    if plan is not None:
        page_refresh = False

        data = {
            "housing_number_type": request.form["housing_number_type"],
            "housing_number_type_display": format_housing_number_type(
                request.form["housing_number_type"]
            ),
            "source_document": request.form["source_document"],
        }

        if "notes" in request.form:
            data["notes"] = request.form["notes"]

        # TODO if this is a joint plan we'll do something about split of housing numbers
        # somewhere in here in the handling of housing numbers I guess?
        if "range" in request.form["housing_number_type"].lower():
            min = request.form.get("min", 0)
            if isinstance(min, str):
                min = min.strip()
            data["min"] = int(min) if min else None
            max = request.form.get("max", 0)
            if isinstance(max, str):
                max = max.strip()
            data["max"] = int(max) if max else None
        else:
            number = request.form.get("number", 0)
            if isinstance(number, str):
                number = number.strip()
            if (
                not plan.is_joint_plan()
                or request.form.get("joint_plan_number_type") == "whole-plan"
            ):
                data["number"] = int(number) if number else None
                message = f"Set housing number to {number} for whole plan"
                page_refresh = True
            else:
                data["housing_number_by_planning_authority"] = {
                    planning_authority: {"number": number}
                }
                message = f"Set housing number to {number} for local authority ({planning_authority})"
                page_refresh = True

        if request.files:
            # only retrieve image if set
            bucket = "local-plans"
            key = f"images/{plan.id}/{uuid.uuid4()}.jpg"
            s3 = boto3.client("s3")
            s3.upload_fileobj(
                request.files["screenshot"],
                bucket,
                key,
                ExtraArgs={"ContentType": "image/jpeg", "ACL": "public-read"},
            )
            data["image_url"] = f"https://s3.eu-west-2.amazonaws.com/{bucket}/{key}"

        if plan.housing_numbers is None:
            data["created_date"] = datetime.datetime.utcnow().isoformat()
        else:
            data["updated_date"] = datetime.datetime.utcnow().isoformat()

        for key, val in data.items():
            if key == "housing_number_by_planning_authority":
                if (
                    plan.housing_numbers.get("housing_number_by_planning_authority")
                    is None
                ):
                    plan.housing_numbers["housing_number_by_planning_authority"] = val
                else:
                    plan.housing_numbers["housing_number_by_planning_authority"] = {
                        **plan.housing_numbers["housing_number_by_planning_authority"],
                        **val,
                    }
            else:
                if plan.housing_numbers is None:
                    plan.housing_numbers = {key: val}
                else:
                    plan.housing_numbers[key] = val

        # Actually I think I can do this in a better and less destructive way in the
        # bit above where the numbers are handled. e.g. if I'm setting a number, remove min/max
        # if setting a min/max remove number
        # if setting a breakdown remove number or min/max
        # lastly if setting a breakdown set split value to None
        to_remove = []
        for key, val in plan.housing_numbers.items():
            if key not in data:
                to_remove.append(key)

        for key in to_remove:
            if key not in ["created_date", "image_url"]:
                plan.housing_numbers.pop(key, None)

        # Again as modifications inside json field not tracked
        # by default flag modified
        flag_modified(plan, "housing_numbers")

        plan.housing_numbers_found = True
        db.session.add(plan)
        db.session.commit()

        if page_refresh:
            plan.housing_numbers["message"] = message

        resp = make_response(jsonify(data=plan.housing_numbers))
        resp.status_code = 200
        resp.headers = {"Content-Type": "application/json"}
        return resp
    else:
        return make_response(jsonify({"error": "could not find plan to update"}), 404)


@frontend.route(
    "/local-plans/<planning_authority>/<plan_id>/update-plan-flags", methods=["POST"]
)
@requires_auth
def update_plan_data_flags(planning_authority, plan_id):
    plan = LocalPlan.query.get(plan_id)

    # TODO plan has two fields, plan_period_found and housing_numbers_found which would at this stage
    # be null. You can set the appropriate flag to False and then save to db

    if plan is not None:
        if request.json.get("data-type") is not None:
            # user saying data can't be found
            found = False if bool(request.json.get("not-found")) else None

            if request.json.get("data-type") == "housing-number":
                plan.housing_numbers_found = found
            else:
                plan.plan_period_found = found

            db.session.add(plan)
            db.session.commit()
            resp = {"OK": 200, "plan": plan.to_dict(planning_authority)}
        else:
            resp = {"OK": 400, "error": "Data type not provided"}
    else:
        resp = {"OK": 400, "error": "Plan not found"}

    return jsonify(resp)


@frontend.route(
    "/local-plans/<planning_authority>/<local_plan>/update-plan-url",
    methods=["GET", "POST"],
)
@requires_auth
def update_local_plan_url(planning_authority, local_plan):
    pla = PlanningAuthority.query.get(planning_authority)
    plan = LocalPlan.query.get(local_plan)
    policy_url = request.json.get("policy-url", "")
    if request.method == "POST" and policy_url:
        plan.url = request.json["policy-url"]
        db.session.add(pla)
        db.session.commit()
        resp = {"OK": 200, "plan": plan.to_dict(pla.id)}
        return jsonify(resp)
    else:
        form = LocalPlanURLForm(url=plan.url)
        if form.validate_on_submit():
            plan.url = form.url.data
            db.session.add(pla)
            db.session.commit()
            return redirect(url_for("frontend.local_plan", planning_authority=pla.id))

    return render_template(
        "update-plan-url.html", planning_authority=pla, local_plan=plan, form=form
    )


@frontend.route(
    "/local-plans/<planning_authority>/<local_plan>/update", methods=["POST"]
)
@requires_auth
def update_plan(planning_authority, local_plan):

    plan_identifier = request.json["new_identifier"].strip()
    original_identifier = request.json["original_identifier"].strip()
    try:
        plan = LocalPlan.query.get(local_plan)
        plan.title = plan_identifier
        db.session.add(plan)
        db.session.commit()
        return jsonify({"message": "plan identifier updated", "OK": 200})
    except Exception as e:
        current_app.logger.exception(e)
        return jsonify(
            {
                "error": "Could not update plan",
                "new_identifier": plan_identifier,
                "original_identifier": original_identifier,
            }
        )


@frontend.route(
    "/local-plans/<planning_authority>/<local_plan>/update-ldf-number", methods=["POST"]
)
@requires_auth
def update_local_development_framework_number(planning_authority, local_plan):
    pla = PlanningAuthority.query.get(planning_authority)
    plan = LocalPlan.query.get(local_plan)
    try:
        ldf_number = request.form.get("local-development-framework-number")
        plan.local_development_framework_number = (
            int(ldf_number) if ldf_number else None
        )
        db.session.add(pla)
        db.session.commit()
        flash("Updated local development framework number")
    except Exception as e:
        flash("Error updating local development framework number")

    plan_tab = f"{url_for('frontend.local_plan', planning_authority=pla.id)}#plan_tab_{local_plan}"
    return redirect(plan_tab)


@frontend.route("/local-plans/data.csv")
def data_as_csv_redirect():
    return redirect(url_for("frontend.data_as_csv"))


@frontend.route("/local-plans/local-plan-data.csv")
def data_as_csv():
    planning_authorities = PlanningAuthority.query.all()
    data = []
    for planning_authority in planning_authorities:
        for plan in planning_authority.sorted_plans():
            d = {
                "planning_authority": planning_authority.id,
                "plan_id": str(plan.id),
                "ons_code": planning_authority.ons_code,
                "name": planning_authority.name,
                "housing_numbers_found": False,
                "plan_period_found": False,
                "plan_title": plan.title,
            }
            if plan.housing_numbers is not None:
                d["housing_numbers_found"] = True
                d["housing_number_type"] = plan.housing_numbers["housing_number_type"]

                if plan.is_joint_plan():
                    if plan.has_joint_plan_breakdown_for_authority(
                        planning_authority.id
                    ):
                        breakdown_number = plan.get_joint_plan_breakdown_for_authority(
                            planning_authority.id
                        )
                        d["number"] = breakdown_number
                    elif not plan.has_joint_plan_breakdown():
                        d["joint_plan_total"] = plan.housing_numbers.get("number", None)
                elif "range" in plan.housing_numbers["housing_number_type"].lower():
                    d["min"] = plan.housing_numbers["min"]
                    d["max"] = plan.housing_numbers["max"]
                else:
                    d["number"] = plan.housing_numbers.get("number", None)

                d["source_document"] = plan.housing_numbers.get("source_document")
                d["cached_source_document"] = plan.housing_numbers.get(
                    "cached_source_document"
                )
                d["source_document_checksum"] = plan.housing_numbers.get(
                    "source_document_checksum"
                )
                d["error_caching_source_document"] = plan.housing_numbers.get(
                    "error_caching_source_document"
                )
                d["notes"] = plan.housing_numbers.get("notes")
                d["screenshot"] = plan.housing_numbers.get("image_url")
                d["created_date"] = plan.housing_numbers.get("created_date")

            if plan.plan_start_year is not None:
                d["start_year"] = plan.plan_start_year.year
            if plan.plan_end_year is not None:
                d["end_year"] = plan.plan_end_year.year

            if plan.plan_start_year is not None and plan.plan_end_year is not None:
                d["plan_period_found"] = True

            d["created_date"] = plan.created_date
            d["updated_date"] = plan.updated_date
            d["is_joint_plan"] = plan.is_joint_plan()
            d["last_updated_by"] = plan.last_updated_by

            if current_app.config["INCLUDE_PINS"]:
                d["published"] = plan.published_date
                d["submitted"] = plan.submitted_date
                d["found_sound"] = plan.sound_date
                d["adopted"] = plan.adopted_date

            d[
                "local_development_framework_number"
            ] = plan.local_development_framework_number

            data.append(d)

    fieldnames = [
        "planning_authority",
        "name",
        "ons_code",
        "plan_title",
        "plan_id",
        "local_development_framework_number",
        "start_year",
        "end_year",
        "plan_period_found",
        "housing_number_type",
        "number",
        "min",
        "max",
        "joint_plan_total",
        "housing_numbers_found",
        "is_joint_plan",
        "source_document",
        "cached_source_document",
        "source_document_checksum",
        "error_caching_source_document",
        "notes",
        "screenshot",
        "created_date",
        "updated_date",
        "last_updated_by",
    ]

    if current_app.config["INCLUDE_PINS"]:
        fieldnames.extend(["published", "submitted", "found_sound", "adopted"])

    with io.StringIO() as output:
        writer = csv.DictWriter(
            output, fieldnames=fieldnames, quoting=csv.QUOTE_ALL, lineterminator="\n"
        )
        writer.writeheader()
        for row in data:
            writer.writerow(row)
        out = make_response(output.getvalue())

    out.headers["Content-Disposition"] = "attachment; filename=local-plan-data.csv"
    out.headers["Content-type"] = "text/csv"
    return out


@frontend.route(
    "/local-plans/<planning_authority>/<local_plan>/make-joint-plan",
    methods=["GET", "POST"],
)
@requires_auth
def make_joint_plan(planning_authority, local_plan):

    planning_authority = PlanningAuthority.query.get(planning_authority)
    link_to_planning_authority = url_for(
        "frontend.local_plan",
        planning_authority=planning_authority.id,
        _anchor=local_plan,
    )
    planning_authorities = (
        PlanningAuthority.query.filter(PlanningAuthority.id != planning_authority.id)
        .order_by(PlanningAuthority.name)
        .all()
    )
    plan = LocalPlan.query.get(local_plan)
    form = MakeJointPlanForm()
    form.planning_authorities.choices = [(p.id, p.name) for p in planning_authorities]

    if form.validate_on_submit():
        for id in form.planning_authorities.data:
            authority = PlanningAuthority.query.get(id)
            if authority not in plan.planning_authorities:
                plan.planning_authorities.append(authority)

        db.session.add(plan)
        db.session.commit()
        return redirect(
            url_for("frontend.local_plan", planning_authority=planning_authority.id)
        )

    return render_template(
        "make-joint-plan.html",
        planning_authority=planning_authority,
        local_plan=plan,
        form=form,
        last_url=link_to_planning_authority,
    )


@frontend.route("/local-plans/<planning_authority>/<local_plan>/remove")
@requires_auth
def remove_plan(planning_authority, local_plan):
    plan = LocalPlan.query.get(local_plan)
    plan.deleted = True
    db.session.add(plan)
    db.session.commit()
    flash(
        Markup(
            f'{plan.title} has been removed. If you want to restore it you can do so from the <a href="/local-plans-removed">list of removed plans</a>.'
        )
    )
    return redirect(
        url_for("frontend.local_plan", planning_authority=planning_authority)
    )


@frontend.route("/local-plans/<planning_authority>/<local_plan>/restore")
@requires_auth
def restore_plan(planning_authority, local_plan):
    plan = LocalPlan.query.get(local_plan)
    plan.deleted = False
    db.session.add(plan)
    db.session.commit()
    return redirect(
        url_for("frontend.local_plan", planning_authority=planning_authority)
    )


@frontend.route("/local-plans-removed")
def removed_plans():
    plans = LocalPlan.query.filter(LocalPlan.deleted == True).all()
    return render_template("removed.html", plans=plans, current_user=get_current_user())


@frontend.route(
    "/local-plans/<planning_authority>/<local_plan>/<state>", methods=["POST"]
)
@requires_auth
def add_pins_state(planning_authority, local_plan, state):
    try:
        d = f"{request.form['pins-state-day']}-{request.form['pins-state-month']}-{request.form['pins-state-year']}"
        date = datetime.datetime.strptime(d, "%d-%m-%Y")
        plan = LocalPlan.query.get(local_plan)
        field = f"{state}_date"
        setattr(plan, field, date)
        db.session.add(plan)
        db.session.commit()
    except Exception as e:
        print("Could not update plan", e)
    return redirect(
        url_for("frontend.local_plan", planning_authority=planning_authority)
    )
