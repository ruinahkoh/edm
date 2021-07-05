import logging
import os

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError

from .file_util import recursive_glob


def download_folder(s3_client, s3_resource, prefix, bucket_name='your_bucket', local='/tmp'):
    """
    Usage:
        s3_client = boto3.client('s3')
        s3_resource = boto3.resource('s3')
        s3_download_folder(s3_client, s3_resource, 'newsletter/2021-01-01/', 'my-bucket', '/tmp')
    """
    paginator = s3_client.get_paginator('list_objects')
    for result in paginator.paginate(Bucket=bucket_name, Delimiter='/', Prefix=prefix):
        if result.get('CommonPrefixes') is not None:
            for subdir in result.get('CommonPrefixes'):
                download_folder(s3_client, s3_resource, subdir.get(
                    'Prefix'), bucket_name, local)
        for file in result.get('Contents', []):
            dest_pathname = os.path.join(local, file.get('Key'))
            if not os.path.exists(os.path.dirname(dest_pathname)):
                os.makedirs(os.path.dirname(dest_pathname))
            s3_resource.meta.client.download_file(
                bucket_name, file.get('Key'), dest_pathname)


def upload_file(s3_client, file_path, bucket_name, object_key=None, config=None):
    """Upload a file to an S3 bucket

    :param file_path: File to upload
    :param bucket_name: Bucket to upload to
    :param object_key: S3 object name including prefix. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_key is None:
        object_key = file_path

    try:
        response = s3_client.upload_file(file_path, bucket_name, object_key)
    except ClientError as e:
        logging.error(e)
        return False
    return True


def upload_folder_content(s3_client, local_folder, bucket_name='your_bucket', s3_folder=''):
    file_paths = recursive_glob(local_folder)
    print(file_paths)
    config = TransferConfig(multipart_threshold=1024 * 25,
                            max_concurrency=10,
                            multipart_chunksize=1024 * 25,
                            use_threads=True)

    for file_path in file_paths:
        print('Uploading {}'.format(file_path))
        upload_file(s3_client, os.path.join(local_folder, file_path), bucket_name,
                    object_key=os.path.join(s3_folder, file_path), config=config)


if __name__ == "__main__":
    s3_client = boto3.client('s3')
    s3_resource = boto3.resource('s3')
    S3_BUCKET = 'emailnewsletterstack-emailnewsletterbucket4e64c92-2qjsd41j79c1'
    S3_FOLDER = 'newsletter'

    # #####
    # Test Upload a File

    # file_name = os.path.join('..', 'newsletter', '2021-01-02', 'raw.json')
    # upload_file(s3_client, file_name, S3_BUCKET, os.path.relpath(file_name, '..'))

    # #####
    # Test Upload a Folder

    upload_folder_content(s3_client, os.path.join(
        '../../data', 'newsletter'), S3_BUCKET, 'temp')

    # #####
    # Test Download a Folder

    # newsletter_date = '2021-01-01'
    # TMP_FOLDER = Path.cwd()
    #
    # # Get Paths
    # template_folder = os.path.join(Path.cwd(), f'app/newsletter/template')
    # data_folder = os.path.join(TMP_FOLDER, S3_FOLDER, newsletter_date)
    # data_file = os.path.join(data_folder, 'data.json')
    # Path(data_folder).mkdir(parents=True, exist_ok=True)
    #
    # # Fetch data_folder of newsletter_date from S3 Bucket to /tmp folder
    # bucket_name = S3_BUCKET
    # download_folder(s3_client, s3_resource, f'{S3_FOLDER}/{newsletter_date}/', bucket_name, TMP_FOLDER)
