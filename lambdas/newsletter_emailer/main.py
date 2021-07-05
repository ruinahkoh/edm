import json
import os
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from urllib.parse import urlparse

import boto3
from dateutil import parser

import config
from utils.s3_util import download_folder, upload_file
from utils.ses_util import send_raw_email

TEMPLATE_FOLDER = '.'
# TMP_FOLDER = 'D:/tmp'
TMP_FOLDER = '/tmp'


def uri_validator(x):
    try:
        result = urlparse(x)
        return all([result.scheme, result.netloc, result.path])
    except:
        return False


def replace_unicode_characters(s):
    mapping = {
        r"\u00a0": " ",
        r"\u2014": "--",
        r"\u2018": "'",
        r"\u2019": "'",
        r"\u201c": r'\"',  # Add \ to escape " in JSON string
        r"\u201d": r'\"'  # Add \ to escape " in JSON string
    }
    for k, v in mapping.items():
        s = s.replace(k, v)

    return s


def construct_message(msg_template_folder, msg_data_file):
    """
    Generate messages in HTML and TEXT format from templates and data
    :param msg_template_folder: Folder which contains template files
    :param msg_data_file: Data file from which message will be contructed
    :return: Messages in HTML and TEXT formats
    """

    # Read Template Files
    item_header_file = os.path.join(msg_template_folder, 'item_header.html')
    with open(item_header_file) as f:
        item_header_html = f.read()

    item_content_file = os.path.join(msg_template_folder, 'item_content.html')
    with open(item_content_file) as f:
        item_content_html = f.read()

    item_text_file = os.path.join(msg_template_folder, 'item.txt')
    with open(item_text_file) as f:
        item_plain = f.read()

    item_fields_file = os.path.join(msg_template_folder, 'item_fields.json')
    with open(item_fields_file) as f:
        fields = json.load(f)

    html_items = []
    text_items = []
    with open(msg_data_file, 'r', encoding='utf-8') as f:
        s = f.read()
        s = replace_unicode_characters(s)
        data = json.loads(s)

    message_text = ''
    message_html = ''
    for row in data:
        img_src_str = row.get(fields.get('img_src', ''), '')
        img_src = img_src_str if uri_validator(
            img_src_str) else f'cid:{img_src_str}'
        img_src = img_src if img_src_str else ''

        # Construct HTML Items
        item_header = item_header_html.format(item_subject=row.get(fields.get('subject', ''), ''),
                                              item_author=row.get(
                                                  fields.get('author', ''), ''),
                                              item_source=row.get(
                                                  fields.get('source', ''), ''),
                                              item_date=row.get(fields.get('date', ''), ''))
        item_content = item_content_html.format(item_abstract=row.get(fields.get('abstract', ''), ''),
                                                item_link=row.get(
                                                    fields.get('link', ''), ''),
                                                item_image_src=img_src)
        html_items.append(item_header + item_content)

        # Construct TEXT Items
        item_text = item_plain.format(item_index='#',
                                      item_subject=row.get(
                                          fields.get('subject', ''), ''),
                                      item_author=row.get(
                                          fields.get('author', ''), ''),
                                      item_source=row.get(
                                          fields.get('source', ''), ''),
                                      item_date=row.get(
                                          fields.get('date', ''), ''),
                                      item_abstract=row.get(
                                          fields.get('abstract', ''), ''),
                                      item_link=row.get(fields.get('link', ''), ''))
        text_items.append(item_text)

        # Construct Newsletter Messages in HTML
        message_html_file = os.path.join(msg_template_folder, 'message.html')
        with open(message_html_file) as f:
            msg_html_template = f.read()
        message_html = msg_html_template.replace(
            '{{items}}', '\n'.join(html_items))

        # Construct Newsletter Messages in Plain TEXT
        message_text_file = os.path.join(msg_template_folder, 'message.txt')
        with open(message_text_file) as f:
            msg_text_template = f.read()
        message_text = msg_text_template.replace(
            '{{items}}', '\n'.join(text_items))

    return message_html, message_text


def construct_and_save_message(msg_template_folder, msg_data_file, msg_html_name='message.html',
                               msg_text_name='message.txt'):
    """
    Construct message in HTML and Text format, save them in the same folder as `msg_data_file`
    :param msg_template_folder: Folder to look for template files
    :param msg_data_file: Data file from which message will be constructed
    :param msg_html_name: File name of output HTML message file
    :param msg_text_name: File name of output TEXT message file
    :return:
    """
    data_folder = os.path.dirname(msg_data_file)
    msg_html_path = os.path.join(data_folder, msg_html_name)
    msg_text_path = os.path.join(data_folder, msg_text_name)

    msg_html, msg_text = construct_message(msg_template_folder, msg_data_file)

    with open(msg_html_path, 'w') as f:
        f.write(msg_html)

    with open(msg_text_path, 'w') as f:
        f.write(msg_text)

    return msg_html_path, msg_text_path


def construct_email(subject, sender, receivers, message_html_file, message_text_file, images_folder="images"):
    """
    Create an instance of MIMEMultipart related-subtype email with subject, from and to addresses
    :param subject: Email subject
    :param sender: Email sender
    :param receivers: List of email addresses
    :param message_html_file: Path to HTML message file
    :param message_text_file: Path to TEXT message file
    :param images_folder: folder name which contains images to be included in email. Image folder must be in the same folder as HTML Message
    :return: Email message
    """
    msg = MIMEMultipart('related')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ','.join(receivers)

    with open(message_html_file) as f:
        message_html = f.read()

    with open(message_text_file) as f:
        message_text = f.read()

    # Set the multipart email preamble attribute value
    msg.preamble = '====================================================='
    # Create a 'alternative' MIMEMultipart object. We will use this object to save plain text format content.
    msg_alternative = MIMEMultipart('alternative')
    # Create a MIMEText object for plain text content
    msg_text = MIMEText(message_text)
    msg_alternative.attach(msg_text)
    # Create a MIMEText object for Html content with images
    msg_text = MIMEText(message_html, 'html')
    msg_alternative.attach(msg_text)
    # Attach the bove object to the root email message.
    msg.attach(msg_alternative)

    # # Add company logo to HTML suing CID
    # company_logo_path = os.path.join(template_path, 'company_logo.gif')
    # company_logo_cid = 'company_logo'
    # with open(company_logo_path, 'rb') as fp:
    #     msgImage = MIMEImage(fp.read())
    #     msgImage.add_header('Content-ID', f'<{company_logo_cid}>')
    #     msg.attach(msgImage)

    # Add other images in data folder
    images_path = os.path.join(os.path.dirname(
        message_html_file), images_folder)
    if os.path.exists(images_path):
        for image_file in os.listdir(images_path):
            image_path = os.path.join(images_path, image_file)
            with open(image_path, 'rb') as fp:
                img_data = MIMEImage(fp.read())
                img_data.add_header('Content-ID', f'<{image_file}>')
            msg.attach(img_data)

    return msg


def handler_construct_upload_message(event, context):
    """
    Construct message from template & data, and upload to S3 bucket
    :param event: In the format of {"newsletter_date": "20210102"}
    :param context:
    :return:
    """
    dt = parser.parse(event['newsletter_date'])
    # newsletter_date in the format of 'YYYY-MM-DD'
    newsletter_date = dt.strftime('%Y-%m-%d')

    # Local folder for Template and Data
    template_folder = os.path.join(
        TMP_FOLDER, config.S3_DATA_FOLDER, 'template')
    data_folder = os.path.join(
        TMP_FOLDER, config.S3_DATA_FOLDER, newsletter_date)
    data_file = os.path.join(data_folder, 'data.json')
    Path(data_folder).mkdir(parents=True, exist_ok=True)
    print('Path:', template_folder, data_folder)

    # Download template and data from S3
    bucket_name = config.S3_DATA_BUCKET
    s3_client = boto3.client('s3')
    s3_resource = boto3.resource('s3')
    # Fetch template_folder and data_folder of newsletter_date from S3 Bucket to /tmp folder
    download_folder(s3_client, s3_resource,
                    f'{config.S3_DATA_FOLDER}/{newsletter_date}/', bucket_name, TMP_FOLDER)
    download_folder(s3_client, s3_resource,
                    f'{config.S3_DATA_FOLDER}/template/', bucket_name, TMP_FOLDER)
    # print('Downloaded S3 files:', [x for x in Path(data_folder).glob('**/*') if x.is_file()])
    # print('Downloaded S3 files:', [x for x in Path(template_folder).glob('**/*') if x.is_file()])

    # Construct HTML and TEXT messages
    message_html_file, message_text_file = construct_and_save_message(
        template_folder, data_file)

    # Upload generated files to S3
    object_key_html = f'{config.S3_DATA_FOLDER}/{newsletter_date}/{Path(message_html_file).name}'
    upload_file(s3_client, message_html_file, bucket_name,
                object_key=object_key_html)
    object_key_text = f'{config.S3_DATA_FOLDER}/{newsletter_date}/{Path(message_text_file).name}'
    upload_file(s3_client, message_text_file, bucket_name,
                object_key=object_key_text)

    return {
        "bucket": bucket_name,
        "html_file": object_key_html,
        "html_text": object_key_text
    }


def handler_download_email_message(event, context):
    """
    Download message HTML and TEXT file, construct an email and send by SES
    :param event: Sample {"to_emails": ["mark.qj@gmail.com"], "newsletter_date": "20210102"}
    :param context:
    :return:
    """
    html_file_name = 'message.html'
    text_file_name = 'message.txt'

    to_emails = event['to_emails']
    dt = parser.parse(event['newsletter_date'])
    # newsletter_date in the format of 'YYYY-MM-DD'
    newsletter_date = dt.strftime('%Y-%m-%d')
    print('Generating newsletter:', newsletter_date, to_emails, type(to_emails))

    # Local folder for Data
    data_folder = os.path.join(
        TMP_FOLDER, config.S3_DATA_FOLDER, newsletter_date)
    data_file = os.path.join(data_folder, 'data.json')
    Path(data_folder).mkdir(parents=True, exist_ok=True)

    # Download template and data from S3
    bucket_name = config.S3_DATA_BUCKET
    s3_client = boto3.client('s3')
    s3_resource = boto3.resource('s3')
    # Fetch template_folder and data_folder of newsletter_date from S3 Bucket to /tmp folder
    download_folder(s3_client, s3_resource,
                    f'{config.S3_DATA_FOLDER}/{newsletter_date}/', bucket_name, TMP_FOLDER)
    # print('Downloaded S3 files:', [x for x in Path(data_folder).glob('**/*') if x.is_file()])

    # Construct HTML and TEXT messages
    message_html_file = os.path.join(data_folder, html_file_name)
    message_text_file = os.path.join(data_folder, text_file_name)

    # Construct and send Email
    subject = config.EMAIL_SUBJECT
    sender = config.EMAIL_ADMIN
    email_object = construct_email(
        subject, sender, to_emails, message_html_file, message_text_file)
    print('Constructed email object')

    # Send Email
    ses_client = boto3.client('ses', region_name=config.SES_REGION)
    result = send_raw_email(ses_client, email_object, sender, to_emails)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            'result': result
        })
    }


def lambda_handler(event, context):
    """
    Construct a message from template and data.
    Upload HTML and TEXT messages to S3 bucket
    Use messages to construct an email and sent it by SES
    :param event: Sample {"to_emails": ["mark.qj@gmail.com"], "newsletter_date": "20210102"}
    :param context:
    :return:
    """
    # ### Processing incoming event from API Gateway
    # body = event['body']
    # event['headers'] = {k.lower(): v.lower() for k, v in event['headers'].items()}
    # if 'headers' in event and 'content-type' in event['headers'] \
    #         and event['headers']['content-type'] == 'application/json' \
    #         and type(body) == str:
    #     print("Convert header to smaller")
    #     body = json.loads(body)
    #     print('Parsing event[body]:', body, )

    to_emails = event.get('to_emails', config.DEFAULT_TO_EMAILS)
    dt = parser.parse(event['newsletter_date'])
    # newsletter_date in the format of 'YYYY-MM-DD'
    newsletter_date = dt.strftime('%Y-%m-%d')
    print('Generating newsletter:', newsletter_date, to_emails, type(to_emails))

    # Local folder for Template and Data
    template_folder = os.path.join(
        TMP_FOLDER, config.S3_DATA_FOLDER, 'template')
    data_folder = os.path.join(
        TMP_FOLDER, config.S3_DATA_FOLDER, newsletter_date)
    data_file = os.path.join(data_folder, 'data.json')
    Path(data_folder).mkdir(parents=True, exist_ok=True)
    print('Path:', template_folder, data_folder)

    # Download template and data from S3
    bucket_name = config.S3_DATA_BUCKET
    s3_client = boto3.client('s3')
    s3_resource = boto3.resource('s3')
    # Fetch template_folder and data_folder of newsletter_date from S3 Bucket to /tmp folder
    download_folder(s3_client, s3_resource,
                    f'{config.S3_DATA_FOLDER}/{newsletter_date}/', bucket_name, TMP_FOLDER)
    download_folder(s3_client, s3_resource,
                    f'{config.S3_DATA_FOLDER}/template/', bucket_name, TMP_FOLDER)
    # print('Downloaded S3 files:', [x for x in Path(data_folder).glob('**/*') if x.is_file()])
    # print('Downloaded S3 files:', [x for x in Path(template_folder).glob('**/*') if x.is_file()])

    # Construct HTML and TEXT messages
    message_html_file, message_text_file = construct_and_save_message(
        template_folder, data_file)

    # Upload generated files to S3
    object_key_html = f'{config.S3_DATA_FOLDER}/{newsletter_date}/{Path(message_html_file).name}'
    upload_file(s3_client, message_html_file, bucket_name,
                object_key=object_key_html)
    object_key_text = f'{config.S3_DATA_FOLDER}/{newsletter_date}/{Path(message_text_file).name}'
    upload_file(s3_client, message_text_file, bucket_name,
                object_key=object_key_text)

    # Construct and send Email
    subject = config.EMAIL_SUBJECT
    sender = config.EMAIL_ADMIN
    email_object = construct_email(
        subject, sender, to_emails, message_html_file, message_text_file)
    print('Constructed email object')

    # Send Email
    ses_client = boto3.client('ses', region_name=config.SES_REGION)
    result = send_raw_email(ses_client, email_object, sender, to_emails)

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            'result': result
        })
    }


if __name__ == "__main__":
    # #### Fix import path issue
    from sys import path
    from os.path import dirname
    path.append(dirname(path[0]))

    # # Testing
    # event = {"newsletter_date": "20210102"}
    # handler_construct_upload_message(event, None)

    # # Testing
    # event = {"to_emails": ["mark.qj@gmail.com"], "newsletter_date": "20210102"}
    # handler_download_email_message(event, None)

    # Testing
    # event = {"to_emails": ["mark.qj@gmail.com"], "newsletter_date": "20210103"}
    event = {"newsletter_date": "20210103"}
    lambda_handler(event, None)
