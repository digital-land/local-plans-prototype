# User journeys

Each file describes one journey through the local plans prototype: who it is for, what they
are trying to do, the steps they take and what they should see. Every journey has acceptance
tests in [`tests/acceptance/`](../../tests/acceptance/) that drive a real browser through the
same steps.

| Journey | Who | Tests |
|---|---|---|
| [Find a local plan](find-a-local-plan.md) | Anyone | [test_find_a_local_plan.py](../../tests/acceptance/test_find_a_local_plan.py) |
| [Add a plan](add-a-plan.md) | Signed in editor | [test_add_a_plan.py](../../tests/acceptance/test_add_a_plan.py) |
| [Edit a plan](edit-a-plan.md) | Signed in editor | [test_edit_a_plan.py](../../tests/acceptance/test_edit_a_plan.py) |
| [Remove and restore a plan](remove-and-restore-a-plan.md) | Signed in editor | [test_remove_and_restore_a_plan.py](../../tests/acceptance/test_remove_and_restore_a_plan.py) |

## Signing in

Editors sign in with Auth0. The tests can't reach Auth0, so they sign the browser in by setting
the same session cookie the Auth0 callback would (see `signed_in_page` in
[`tests/conftest.py`](../../tests/conftest.py)). The sign in step itself is not covered.

## Running the tests

The tests need a Postgres database and a Chromium browser:

    createdb local_plans_test
    playwright install chromium
    pytest tests/acceptance

Set `TEST_DATABASE_URL` to use a database other than `postgresql://localhost/local_plans_test`.
Add `--headed` to watch the browser.
