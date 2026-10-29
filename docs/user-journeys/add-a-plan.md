# Add a plan

**Who:** a signed in editor.

**Goal:** record a new local plan for a planning authority.

## Steps

1. Go to the planning authority's page.
2. Choose the "Add new plan" tab.
3. Enter the plan title, start year and end year. The local development framework number is
   optional.
4. Choose "Add plan".

## What they should see

- The planning authority's page again, with a tab for the new plan showing its title and
  plan period.

## When something goes wrong

- If the title, start year or end year is missing, the browser asks them to fill it in
  before the form is sent, and no plan is added. (If the form is sent anyway, the server
  shows it again with an error next to each missing field.)

## Who can't do this

- Signed out users don't see the "Add new plan" tab. If they send the form anyway, they are
  sent to sign in and no plan is added.

## Tests

[tests/acceptance/test_add_a_plan.py](../../tests/acceptance/test_add_a_plan.py)
