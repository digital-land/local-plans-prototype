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



User management and authenication
----------------------

Auth0 user for user managment and authenication

If you have a Heroku account and are a member of the Digial Land Heroku organisation you can access the dashboard,
click on Auth0 add-on and manager users [here](https://dashboard.heroku.com/apps/local-plans-prototype/resources)

    
Load updates from PINS
----------------------

The local plans team will provide monthly updates from PINS as csv files. The
files should be renamed pins-local-plans-[MON]-2019.csv, committed to the data directory 
and once deployed the following command should be run on heroku:

```
flask pins_update --pinscsv pins-local-plans-[MON]-2019.csv
```

The output should be sent to Local Plans team

Data backups
------------

[Download a .csv version of the data](https://local-plans-prototype.herokuapp.com/local-plans/local-plan-data.csv).

Heroku backs up the database every night. You can download backups from the Heroku admin interface.

You can also run and download a backup from the terminal:

    heroku pg:backups:capture -a local-plans-prototype
    heroku pg:backups:download -a local-plans-prototype
