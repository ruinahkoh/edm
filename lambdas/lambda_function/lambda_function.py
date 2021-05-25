import boto3
import requests
import json
from requests_aws4auth import AWS4Auth

region = 'ap-southeast-1'
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

# host = 'https://vpc-edm-57fgkf6gzi534epw4xql3rjdym.ap-southeast-1.es.amazonaws.com' # the Amazon ES domain, with https://
host = 'https://search-edmarticlesearch-qz34ik5dlxmbfdzcsqmw477x2q.ap-southeast-1.es.amazonaws.com'
index = 'articles'
type = '_doc'
url = host + '/' + index + '/' + type + '/'

headers = { "Content-Type": "application/json" }

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
            document_json = {
                'date': document['date']['S'],
                'url': document['url']['S'],
                'text': document['text']['S'],
                'blurp':document['blurp']['S'],
                'imgurl':document['imgurl']['S'],
                'title':document['title']['S'],
                'tags':document['tag']['S'],
                'category':document['category']['S']


            }
            r = requests.put(url + id, auth=awsauth, json=document_json, headers=headers)
        count += 1
    
    print('Request completed ...')
    print(r)
    print(r.text)