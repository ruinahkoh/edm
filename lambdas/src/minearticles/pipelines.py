# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html


# class MinearticlesPipeline(object):
#     def process_item(self, item, spider):
#         return item

from io import BytesIO
from urllib.parse import urlparse
from datetime import datetime
import gzip

import boto3
from botocore.exceptions import ClientError

from scrapy.exporters import JsonLinesItemExporter

class S3Pipeline:
    """
    Scrapy pipeline to store items into S3 bucket with JSONLines format.
    Unlike FeedExporter, the pipeline has the following features:
    * The pipeline stores items by chunk.
    * Support GZip compression.
    """

    def __init__(self, settings, stats):
        self.stats = stats

        url = settings['S3PIPELINE_URL']
        o = urlparse(url)
        self.bucket_name = o.hostname
        self.object_key_template = o.path[1:]  # Remove the first '/'

        self.max_chunk_size = settings.getint('S3PIPELINE_MAX_CHUNK_SIZE', 100)
        self.use_gzip = settings.getbool('S3PIPELINE_GZIP', url.endswith('.gz'))

        self.s3 = boto3.client(
            's3',
            region_name=settings['AWS_REGION_NAME'], use_ssl=settings['AWS_USE_SSL'],
            verify=settings['AWS_VERIFY'], endpoint_url=settings['AWS_ENDPOINT_URL'],
            aws_access_key_id=settings['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=settings['AWS_SECRET_ACCESS_KEY'])
        self.items = []
        self.chunk_number = 0

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings, crawler.stats)

    def process_item(self, item, spider):
        """
        Process single item. Add item to items and then upload to S3 if size of items
        >= max_chunk_size.
        """
        self.items.append(item)
        if len(self.items) >= self.max_chunk_size:
            self._upload_chunk(spider)

        return item

    def open_spider(self, spider):
        """
        Callback function when spider is open.
        """
        # Store timestamp to replace {time} in S3PIPELINE_URL
        self.ts = datetime.utcnow().replace(microsecond=0).isoformat().replace(':', '-')

    def close_spider(self, spider):
        """
        Callback function when spider is closed.
        """
        # Upload remained items to S3.
        self._upload_chunk(spider)

    def _upload_chunk(self, spider):
        """
        Do upload items to S3.
        """

        if not self.items:
            return  # Do nothing when items is empty.

        f = self._make_fileobj()

        # Build object key by replacing variables in object key template.
        object_key = self.object_key_template.format(**self._get_uri_params(spider))

        try:
            self.s3.upload_fileobj(f, self.bucket_name, object_key)
        except ClientError:
            self.stats.inc_value('pipeline/s3/fail')
            raise
        else:
            self.stats.inc_value('pipeline/s3/success')
        finally:
            # Prepare for the next chunk
            self.chunk_number += len(self.items)
            self.items = []

    def _get_uri_params(self, spider):
        params = {}
        for key in dir(spider):
            params[key] = getattr(spider, key)

        params['chunk'] = self.chunk_number
        params['time'] = self.ts
        return params

    def _make_fileobj(self):
        """
        Build file object from items.
        """

        bio = BytesIO()
        f = gzip.GzipFile(mode='wb', fileobj=bio) if self.use_gzip else bio

        # Build file object using ItemExporter
        exporter = JsonLinesItemExporter(f)
        exporter.start_exporting()
        for item in self.items:
            exporter.export_item(item)
        exporter.finish_exporting()

        if f is not bio:
            f.close()  # Close the file if GzipFile

        # Seek to the top of file to be read later
        bio.seek(0)

        return bio

def default_encoder(value):
    if isinstance(value, datetime.datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    elif isinstance(value, datetime.date):
        return value.strftime('%Y-%m-%d')
    elif isinstance(value, datetime.time):
        return value.strftime('%H:%M:%S')
    else:
        return value


class DynamoDbPipeline(object):

    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name,
                 table_name, endpoint_url, encoder=default_encoder):
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region_name = region_name
        self.table_name = table_name
        self.endpoint_url = endpoint_url
        self.encoder = encoder
        self.table = None

    @classmethod
    def from_crawler(cls, crawler):
        aws_access_key_id = crawler.settings['AWS_ACCESS_KEY_ID']
        aws_secret_access_key = crawler.settings['AWS_SECRET_ACCESS_KEY']
        region_name = crawler.settings['DYNAMODB_PIPELINE_REGION_NAME']
        table_name = crawler.settings['DYNAMODB_PIPELINE_TABLE_NAME']
        endpoint_url = crawler.settings['DYNAMODB_ENDPOINT_URL']
        return cls(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
            table_name=table_name,
            endpoint_url=endpoint_url
        )

    def open_spider(self, spider):
        # print('[DEB]', 'openspider')
        db = boto3.resource(
            'dynamodb',
            region_name=self.region_name
        )
        self.table = db.Table(self.table_name)  # pylint: disable=no-member

    def close_spider(self, spider):
        self.table = None

    def process_item(self, item, spider):
        # print('[DEB]', 'processitem')
        self.table.put_item(
            TableName=self.table_name,
            Item=item
        )
        return item





