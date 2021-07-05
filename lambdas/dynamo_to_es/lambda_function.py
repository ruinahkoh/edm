# Function to store all new articles into the elasticsearch
import boto3
import requests
import json
from datetime import datetime
from requests_aws4auth import AWS4Auth

region = 'ap-southeast-1'
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key,
                   region, service, session_token=credentials.token)

# host = 'https://vpc-edm-57fgkf6gzi534epw4xql3rjdym.ap-southeast-1.es.amazonaws.com' # the Amazon ES domain, with https://
host = 'https://search-edmarticlesearch-qz34ik5dlxmbfdzcsqmw477x2q.ap-southeast-1.es.amazonaws.com'
index = 'new_index'
type = '_doc'
url = host + '/' + index + '/' + type + '/'

headers = {"Content-Type": "application/json"}


def lambda_handler(event, context):
    count = 0
    print(event)
    for record in event['Records']:
        # Get the primary key for use as the Elasticsearch ID
        id = record['dynamodb']['Keys']['title']['S']
        # id = "1"

        if record['eventName'] == 'REMOVE':
            r = requests.delete(url + id, auth=awsauth)
        else:
            document = record['dynamodb']['NewImage']
            print(document)
            # elastic search requires date format to be standard to recognise dates
            date = document['date'].get('S')
            date = datetime.strftime(
                datetime.strptime(date, "%d/%m/%Y"), "%Y-%m-%d")
            print(date)
            try:
                tags = document['tags'].get('S')
            except IndexError:
                tags = document['tags'].get('NULL')

            document_json = {
                'date': date,
                'url': document['url'].get('S'),
                'text': document['text'].get('S'),
                'blurp': document['blurp'].get('S'),
                'imgurl': document['imgurl'].get('S'),
                'title': document['title'].get('S'),
                'tags': tags,
                'category': document['category'].get('S')
            }
            r = requests.put(url + id, auth=awsauth,
                             json=document_json, headers=headers)
        count += 1

    print('Request completed ...')
    print(r)
    print(r.text)
