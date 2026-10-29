import datetime

import pytest

from application.extensions import db as _db
from application.factory import create_app
from application.models import LocalPlan, PlanningAuthority

TEST_USER = {
    "user_id": "auth0|test-user",
    "name": "Test User",
    "nickname": "test-user",
    "picture": "",
}


@pytest.fixture(scope="session")
def app():
    """App configured with config.TestConfig, against an empty test database."""
    application = create_app("config.TestConfig")

    with application.app_context():
        _db.drop_all()
        _db.create_all()
        # don't share pooled connections with the forked live server process
        _db.engine.dispose()

    yield application

    with application.app_context():
        _db.drop_all()


@pytest.fixture(autouse=True)
def clean_db(app):
    """Empty every table after each test so tests don't depend on each other."""
    yield
    with app.app_context():
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture
def planning_authority(app):
    with app.app_context():
        pla = PlanningAuthority(
            id="local-authority-eng:TST",
            ons_code="E07000999",
            name="Testshire District Council",
            website="https://www.testshire.gov.uk",
        )
        _db.session.add(pla)
        _db.session.commit()
        return {"id": pla.id, "name": pla.name}


@pytest.fixture
def local_plan(app, planning_authority):
    with app.app_context():
        pla = _db.session.get(PlanningAuthority, planning_authority["id"])
        plan = LocalPlan(
            title="Testshire Local Plan 2020-2035",
            url="https://www.testshire.gov.uk/local-plan",
            plan_start_year=datetime.date(2020, 1, 1),
            plan_end_year=datetime.date(2035, 1, 1),
            local_development_framework_number=1234,
        )
        plan.planning_authorities.append(pla)
        _db.session.add(plan)
        _db.session.commit()
        return {"id": str(plan.id), "title": plan.title}


def get_local_plan(app, plan_id):
    """Read a plan straight from the database, to check what a journey saved."""
    with app.app_context():
        plan = _db.session.get(LocalPlan, plan_id)
        _db.session.expunge(plan)
        return plan


@pytest.fixture
def signed_in_page(app, live_server, page):
    """A browser page signed in as TEST_USER.

    Signing in normally goes through Auth0, which tests can't reach, so this sets
    the same signed session cookie the Auth0 callback would.
    """
    serializer = app.session_interface.get_signing_serializer(app)
    page.context.add_cookies(
        [
            {
                "name": app.config["SESSION_COOKIE_NAME"],
                "value": serializer.dumps({"profile": TEST_USER}),
                "url": live_server.url(),
            }
        ]
    )
    return page
