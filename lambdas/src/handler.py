
import sys
import imp
import os
import logging
import time
import datetime
import boto3
from urllib.parse import urlparse
from scrapy.spiderloader import SpiderLoader
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Need to "mock" sqlite for the process to not crash in AWS Lambda / Amazon Linux
sys.modules["sqlite"] = imp.new_module("sqlite")
sys.modules["sqlite3.dbapi2"] = imp.new_module("sqlite.dbapi2")

def hello():
    return{'message':'hi there'}

def is_in_aws():
    return os.getenv('AWS_EXECUTION_ENV') is not None


def crawl(event, context):
    settings = {}
    spider_kwargs = {}
    
    project_settings = get_project_settings()
    spider_loader = SpiderLoader(project_settings)
    
    spider_name = event['spider_name']
    spider_cls = spider_loader.load(spider_name)
    
    feed_uri = ""
    feed_format = "json"
   
    try:
        spider_key = spider_name
        # urlparse(spider_cls.start_urls[0]).hostname
        # if spider_kwargs.get("start_urls") else urlparse(spider_cls.start_urls[0]).hostname
    except Exception:
        logging.exception("Spider or kwargs need start_urls.")

    if is_in_aws():
		# Lambda can only write to the /tmp folder.
        settings['HTTPCACHE_DIR'] =  "/tmp"
        feed_uri = "s3://edmscraperbucket/scraper_feed_bucket/{}/%(time)s.json".format(spider_name)
        table_name = 'Articles'
    else:
        feed_uri = "file://{}/%(name)s-{}-%(time)s.json".format(
            os.path.join(os.getcwd(), "data/output_current"),
            spider_key,
        )
        # feed_uri = f"s3://{os.getenv('FEED_BUCKET_NAME')}/%(name)s-{spider_key}.json"
        # feed_uri = "s3://my-sls-scraper-dev-scraperfeedbucket-jh1z1v9u3h0d/{}/%(name)s-%(time)s.json".format(
        feed_uri = "s3://edmscraperbucket/scraper_feed_bucket/{}/%(time)s.json".format(spider_name)

    settings['DYNAMODB_PIPELINE_TABLE_NAME'] = table_name
    settings['FEED_URI'] = feed_uri
    settings['FEED_FORMAT'] = feed_format

    process = CrawlerProcess({**project_settings, **settings})

    process.crawl(spider_cls, **spider_kwargs)
    process.start()
    
    time.sleep(10)


