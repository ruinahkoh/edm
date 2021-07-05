import os

import dotenv

dotenv.load_dotenv()

S3_DATA_BUCKET = os.environ['S3_DATA_BUCKET']
S3_DATA_FOLDER = os.environ['S3_DATA_FOLDER']

SES_REGION = os.environ['SES_REGION']
LAMBDA_REGION = os.environ['LAMBDA_REGION']

EMAIL_SUBJECT = os.environ['EMAIL_SUBJECT']
EMAIL_ADMIN = os.environ['EMAIL_ADMIN']

DEFAULT_TO_EMAILS = os.environ.get('DEFAULT_TO_EMAILS', '')
DEFAULT_TO_EMAILS = DEFAULT_TO_EMAILS.split(',') if DEFAULT_TO_EMAILS else []
