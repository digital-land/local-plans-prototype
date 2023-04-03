FLASK_ENV=development
FLASK_DEBUG=True
FLASK_CONFIG=config.DevelopmentConfig
FLASK_APP=application.wsgi:app
SECRET_KEY=replaceinprod
DATABASE_URL=postgresql://localhost/local_plans
S3_REGION=eu-west-1
S3_BUCKET=digital-land-output
