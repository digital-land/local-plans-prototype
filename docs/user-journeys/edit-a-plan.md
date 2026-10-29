# Edit a plan

**Who:** a signed in editor.

**Goal:** correct the details of an existing plan.

## Change the plan period

1. Go to the planning authority's page and choose the plan's tab.
2. Under the plan period, choose "Update plan period".
3. Change the start year and end year.
4. Choose "Save plan period".

The new plan period is shown straight away, without reloading the page, and is saved.

## Change the local development framework number

1. Go to the planning authority's page and choose the plan's tab.
2. Under the local development framework number, choose "Update local development framework
   number" (or "please add it" if the plan doesn't have one yet).
3. Enter the new number.
4. Choose "Save".

The page reloads showing the new local development framework number.

## Who can't do this

- Signed out users don't see the "Update" links. The update addresses send them to sign in
  without changing the plan.

## Tests

[tests/acceptance/test_edit_a_plan.py](../../tests/acceptance/test_edit_a_plan.py)
