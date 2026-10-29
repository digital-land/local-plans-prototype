# Remove and restore a plan

**Who:** a signed in editor.

**Goal:** take a plan out of the data (for example a duplicate or a plan added by mistake), and
put it back if that was wrong.

Removing a plan doesn't delete it. It is hidden from the planning authority's page and left out
of the CSV export, and it can be restored.

## Remove a plan

1. Go to the planning authority's page and choose the plan's tab.
2. Choose "Remove this plan".

They should see the planning authority's page without the plan, and a message saying the plan
has been removed, with a link to the list of removed plans.

## Restore a plan

1. Go to the list of removed plans (from the link in the message, or "Removed plans" on the
   home page).
2. Find the plan. It shows who removed it.
3. Choose "restore".

They should see the planning authority's page with the plan back in it.

## Who can't do this

- Signed out users don't see the "Remove this plan" button, and the removed plans list shows
  "Login to restore plans" instead of restore links.
- The remove and restore addresses send signed out users to sign in without changing the plan.

## Tests

[tests/acceptance/test_remove_and_restore_a_plan.py](../../tests/acceptance/test_remove_and_restore_a_plan.py)
