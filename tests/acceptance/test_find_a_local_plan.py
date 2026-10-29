"""Journey: docs/user-journeys/find-a-local-plan.md"""

from playwright.sync_api import expect


def test_anyone_can_find_a_planning_authoritys_local_plan(
    live_server, page, planning_authority, local_plan
):
    page.goto(live_server.url("/"))
    page.get_by_role(
        "link", name="View or enter housing number data for planning authorities"
    ).click()

    page.get_by_role("link", name=local_plan["title"]).click()

    expect(page.get_by_role("heading", level=1)).to_have_text(
        planning_authority["name"]
    )
    plan_tab = page.locator(f"#plan_tab_{local_plan['id']}")
    expect(plan_tab.get_by_role("heading", name=local_plan["title"])).to_be_visible()
    expect(plan_tab.locator(".policy-url")).to_have_text(
        "https://www.testshire.gov.uk/local-plan"
    )
    expect(plan_tab.locator(".plan-period")).to_have_text("2020-2035")
    expect(plan_tab).to_contain_text("Local development framework number: 1234")


def test_signed_out_users_see_no_editing_controls(
    live_server, page, planning_authority, local_plan
):
    page.goto(live_server.url(f"/local-plans/{planning_authority['id']}"))

    expect(page.get_by_role("link", name="Login to edit this page")).to_be_visible()
    expect(page.get_by_role("tab", name="Add new plan")).to_have_count(0)
    expect(page.get_by_role("link", name="Remove this plan")).to_have_count(0)
    expect(page.get_by_role("link", name="Update plan period")).to_have_count(0)
