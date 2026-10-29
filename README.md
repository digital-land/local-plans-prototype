# local-plan-prototype

Requirements

- [Python 3.13](https://www.python.org/)
- [Node](https://nodejs.org/en/) LTS (version in `.nvmrc`) and [Npm](https://www.npmjs.com/)
- Postgres

Getting started
---------------

Install front end build tool (gulp)

    npm install

Make a virtualenv for the project (the Python version is in `.python-version`) and install python dependencies

    pip install -r requirements/requirements.txt -r requirements/dev-requirements.txt

Generate CSS

    npm run scss

Run flask server

    flask run


Create database and install PostGIS extensions

```
createdb local_plans
```

Using `psql -d local_plans`, run:

    CREATE EXTENSION postgis;

Check if all went well

    SELECT PostGIS_Version();

You should see something similar to:

    2.4 USE_GEOS=1 USE_PROJ=1 USE_STATS=1   
    
    
Environment variables in .flaskenv already set

    FLASK_ENV=development
    FLASK_CONFIG=config.DevelopmentConfig
    FLASK_APP=application.wsgi:app
    SECRET_KEY=replaceinprod
    DATABASE_URL=postgresql://localhost/local_plans

Additional environment variables to add to .env (gitignored)

    AWS_ACCESS_KEY_ID=[your access key]
    AWS_SECRET_ACCESS_KEY=[your secret access key]
    MAPBOX_TOKEN=[your map box token]

Build tasks
-----------

We use gulp to compile and generate a lot of the assets.

There are tasks to do this.

Get a list of the available tasks with:

    npx gulp --tasks

Lint the JavaScript (ESLint) and SCSS (stylelint) sources with:

    npm run lint

Tests
-----

Acceptance tests for the main user journeys are in `tests/acceptance`, and the journeys
they cover are described in [docs/user-journeys](docs/user-journeys/README.md). They drive
a real browser with Playwright, against a Postgres test database:

    createdb local_plans_test
    playwright install chromium
    make test-acceptance

Set `TEST_DATABASE_URL` to use a database other than `postgresql://localhost/local_plans_test`.
They run in GitHub Actions (`.github/workflows/test.yml`) on every push to a branch other
than `master`.

Docker
------

The image runs the app with gunicorn using `config.Config`, which holds the safe
defaults for deployed environments (debug off, secure cookies). `DevelopmentConfig` and
`TestConfig` override these for local development and CI.

It needs `DATABASE_URL` and `SECRET_KEY` set, and serves on port 5050 (override with `PORT`).
HTTPS is enforced by CloudFront, so the app does not redirect HTTP to HTTPS unless
`HTTPS_REDIRECT=true` is set. This keeps load balancer health checks on `/` working.

    docker build -t local-plans-prototype .
    docker run -p 5050:5050 -e DATABASE_URL=... -e SECRET_KEY=... local-plans-prototype



User management and authentication
----------------------------------

Users and logins are managed in [Auth0](https://auth0.com/). To add or remove users,
use the Auth0 dashboard for the tenant set in `AUTH0_DOMAIN`. The app needs
`AUTH0_CLIENT_ID`, `AUTH0_CLIENT_SECRET`, `AUTH0_DOMAIN` and `AUTH0_CALLBACK_URL` set,
and only requires a login when `AUTHENTICATION_ON=true`.

Load updates from PINS
----------------------

PINS updates were provided as monthly csv files until October 2019. The command to
load one is still available. Put the file in the `data` directory and run it locally
with `DATABASE_URL` pointing at the database to update:

```
flask pins_update --pinscsv pins-local-plans-[MON]-[YEAR].csv
```

Deployment
----------

The app is deployed to AWS ECS by the GitHub Actions workflow in `.github/workflows/deploy.yml`,
which builds the Docker image and pushes it to ECR.

Data
----

A csv of all the data can be downloaded from `/local-plans/local-plan-data.csv` on the live site.

`data/database_backup.dump` is the last backup taken from the previous Heroku hosting.
Restore it into a local database with:

    pg_restore --no-owner --no-acl -d local_plans data/database_backup.dump
