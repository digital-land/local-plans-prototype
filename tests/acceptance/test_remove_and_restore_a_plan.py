"""Journey: docs/user-journeys/remove-and-restore-a-plan.md"""

from playwright.sync_api import expect

from tests.conftest import TEST_USER, get_local_plan


def test_editor_can_remove_and_restore_a_plan(
    app, live_server, signed_in_page, planning_authority, local_plan
):
    page = signed_in_page
    page.goto(live_server.url(f"/local-plans/{planning_authority['id']}"))

    # remove
    page.get_by_role("link", name="Remove this plan").click()

    expect(page.locator(".flash-messages")).to_contain_text(
        f"{local_plan['title']} has been removed"
    )
    expect(page.locator(f"#plan_tab_{local_plan['id']}")).to_have_count(0)
    assert get_local_plan(app, local_plan["id"]).deleted is True

    # restore
    page.get_by_role("link", name="list of removed plans").click()

    removed = page.get_by_role("listitem").filter(has_text=local_plan["title"])
    expect(removed).to_contain_text(f"Removed by {TEST_USER['nickname']}")
    removed.get_by_role("link", name="restore").click()

    expect(page.get_by_role("heading", level=1)).to_have_text(
        planning_authority["name"]
    )
    expect(page.locator(f"#plan_tab_{local_plan['id']}")).to_be_attached()
    assert get_local_plan(app, local_plan["id"]).deleted is False


def test_signed_out_users_cannot_remove_or_restore_a_plan(
    app, live_server, page, client, planning_authority, local_plan
):
    base = f"/local-plans/{planning_authority['id']}/{local_plan['id']}"

    for action in ("remove", "restore"):
        response = client.get(f"{base}/{action}")
        assert response.status_code == 302
        assert "/auth/login" in response.location
    assert get_local_plan(app, local_plan["id"]).deleted is False

    page.goto(live_server.url("/local-plans-removed"))
    expect(page.get_by_role("link", name="Login to restore plans")).to_be_visible()
