# local-plan-prototype

Requirements

- [Python 3](https://www.python.org/)
- [Node](https://nodejs.org/en/) and [Npm](https://www.npmjs.com/)
- Postgres

Getting started
---------------

Install front end build tool (gulp)

    npm install

Make a virtualenv for the project and install python dependencies

    pip install -r requirements.txt

Generate CSS

    gulp scss

Run flask server

    flask run


Create database and install PostGIS extensions

Create a local postgres db

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

    gulp --tasks
