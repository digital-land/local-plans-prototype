"""Journey: docs/user-journeys/edit-a-plan.md"""

from playwright.sync_api import expect

from tests.conftest import get_local_plan


def test_editor_can_change_the_plan_period(
    app, live_server, signed_in_page, planning_authority, local_plan
):
    page = signed_in_page
    page.goto(live_server.url(f"/local-plans/{planning_authority['id']}"))
    plan_tab = page.locator(f"#plan_tab_{local_plan['id']}")

    plan_tab.get_by_role("link", name="Update plan period").click()
    # the labels' "for" don't match the input ids, so find the inputs by name
    plan_tab.locator("input[name^='start-year_edit']").fill("2021")
    plan_tab.locator("input[name^='end-year_edit']").fill("2036")
    plan_tab.get_by_role("button", name="Save plan period").click()

    expect(plan_tab.locator(".plan-period").first).to_have_text("2021-2036")

    plan = get_local_plan(app, local_plan["id"])
    assert plan.plan_start_year.year == 2021
    assert plan.plan_end_year.year == 2036


def test_editor_can_change_the_local_development_framework_number(
    app, live_server, signed_in_page, planning_authority, local_plan
):
    page = signed_in_page
    page.goto(live_server.url(f"/local-plans/{planning_authority['id']}"))
    plan_tab = page.locator(f"#plan_tab_{local_plan['id']}")

    plan_tab.get_by_role(
        "link", name="Update local development framework number"
    ).click()
    plan_tab.get_by_label("Local development framework number").fill("5678")
    plan_tab.locator(".edit-local-development-framework-number").get_by_role(
        "button", name="Save"
    ).click()

    expect(plan_tab).to_contain_text("Local development framework number: 5678")
    assert (
        get_local_plan(app, local_plan["id"]).local_development_framework_number == 5678
    )


def test_signed_out_users_cannot_edit_a_plan(
    app, client, planning_authority, local_plan
):
    base = f"/local-plans/{planning_authority['id']}/{local_plan['id']}"

    period = client.post(
        f"{base}/update-plan-period", json={"start-year": "1999", "end-year": "2000"}
    )
    ldf = client.post(
        f"{base}/update-ldf-number", data={"local-development-framework-number": "1"}
    )

    for response in (period, ldf):
        assert response.status_code == 302
        assert "/auth/login" in response.location
    plan = get_local_plan(app, local_plan["id"])
    assert plan.plan_start_year.year == 2020
    assert plan.local_development_framework_number == 1234
