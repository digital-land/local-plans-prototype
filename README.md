# local-plan-prototype

Requirements

- [Python 3](https://www.python.org/)
- [Node](https://nodejs.org/en/) and [Npm](https://www.npmjs.com/)

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


Install PostGIS extensions

If you're using Postgres.app on OSX it should be installed already but you'll need to add it to the brownfield db. Using `psql -d brownfield`, run:

    CREATE EXTENSION postgis;

Check if all went well

    SELECT PostGIS_Version();

You should see something similar to:

    2.4 USE_GEOS=1 USE_PROJ=1 USE_STATS=1