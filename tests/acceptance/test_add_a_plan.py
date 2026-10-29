"""Journey: docs/user-journeys/add-a-plan.md"""

from playwright.sync_api import expect

from application.extensions import db
from application.models import LocalPlan


def plan_titles(app):
    with app.app_context():
        return [p.title for p in db.session.query(LocalPlan).all()]


def test_editor_can_add_a_plan(app, live_server, signed_in_page, planning_authority):
    page = signed_in_page
    page.goto(live_server.url(f"/local-plans/{planning_authority['id']}"))

    page.get_by_role("tab", name="Add new plan").click()
    page.get_by_label("Plan title").fill("Testshire Local Plan 2025-2040")
    page.get_by_label("Start year").fill("2025")
    page.get_by_label("End year").fill("2040")
    page.get_by_label("Local development framework number").fill("42")
    page.get_by_role("button", name="Add plan").click()

    expect(
        page.get_by_role("tab", name="Testshire Local Plan 2025-2040")
    ).to_be_visible()
    expect(page.locator(".plan-period").first).to_have_text("2025-2040")

    with app.app_context():
        plan = db.session.query(LocalPlan).one()
        assert plan.title == "Testshire Local Plan 2025-2040"
        assert plan.plan_start_year.year == 2025
        assert plan.plan_end_year.year == 2040
        assert plan.local_development_framework_number == 42
        assert [pa.id for pa in plan.planning_authorities] == [planning_authority["id"]]


def test_missing_details_must_be_filled_in(
    app, live_server, signed_in_page, planning_authority
):
    page = signed_in_page
    page.goto(live_server.url(f"/local-plans/{planning_authority['id']}"))

    page.get_by_role("tab", name="Add new plan").click()
    page.get_by_label("Start year").fill("2025")
    page.get_by_role("button", name="Add plan").click()

    # the browser won't send the form until the required fields are filled in
    for label in ("Plan title", "End year"):
        assert page.get_by_label(label).evaluate("el => !el.validity.valid")
    assert page.get_by_label("Start year").evaluate("el => el.validity.valid")
    assert plan_titles(app) == []


def test_signed_out_users_cannot_add_a_plan(app, client, planning_authority):
    response = client.post(
        f"/local-plans/{planning_authority['id']}",
        data={"title": "Not allowed", "start_year": "2025", "end_year": "2040"},
    )

    assert response.status_code == 302
    assert "/auth/login" in response.location
    assert plan_titles(app) == []
