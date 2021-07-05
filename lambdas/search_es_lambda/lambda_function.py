import boto3
import requests
import json
from datetime import date, datetime, timedelta
from requests_aws4auth import AWS4Auth
import typing

region = 'ap-southeast-1'
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key,
                   region, service, session_token=credentials.token)

# host = 'https://vpc-edm-57fgkf6gzi534epw4xql3rjdym.ap-southeast-1.es.amazonaws.com' # the Amazon ES domain, with https://
host = 'https://search-edmarticlesearch-qz34ik5dlxmbfdzcsqmw477x2q.ap-southeast-1.es.amazonaws.com'
index = 'new_index'
type = '_doc'
# url = host + '/' + index + '/' + type + '/'
url = host + '/' + index + '/_search'
headers = {"Content-Type": "application/json"}

days = timedelta(1)
current_date = date.today()
query_date = current_date - days
query_date = datetime.strftime(query_date, '%Y-%m-%d')


def lambda_handler(event, context):
    keywords = ['einvoicing',
                'blockchain',
                'digital id',
                'artificial intelligence governance',
                'dataflows',
                'data privacy',
                'data security',
                '5g']
    recommended = {}
    seen = {}
    score={}
    for word in keywords:
        Data = getData(word, query_date)
        # print(Data)
        # print(Data["hits"]["hits"])
        for hit in Data['hits']['hits']:  # loop the data
            print("Article Name-->", hit['_source']['title'])
            hit['_source']['score'] = hit['_score']
            title = hit['_source']['title']
            # hit['_source']['keyword'] = word
            # remove the duplicate articles
            if title not in seen:
                seen[title] = set([word])
                score[title] = hit['_score']
                hit['_source']['avg_score'] = score[title]
                hit['_source']['keyword'] = [word]
                recommended[title] = hit['_source']
            elif title in seen:
                print(seen.get(title))
                seen.get(title).add(word)
                score[title] += hit['_score']
                print(score[title])
                hit['_source']['score'] = score[title]
                hit['_source']['avg_score'] = score[title]/len(seen.get(title))
                hit['_source']['keyword'] = list(seen[title])
                recommended[title] = hit['_source']
    recommended = list(recommended.values())
    print(recommended)

    bucket_name = 'edmscraperbucket'
    s3 = boto3.resource('s3')
    file_name = 'ES_output/' + str(current_date) + '/' + 'data.json'
    object = s3.Object(bucket_name, file_name)
    object.put(Body=(bytes(json.dumps(recommended, indent=2).encode('UTF-8'))))

    # Trigger lambda to email newsletter
    payload = {"newsletter_date": str(current_date)}

    response = invoke_lambda(func_name='newsletter_emailer',
                             payload=payload)
    print(f'response:{response}')


# getData() will return the elasticSearch result


def invoke_lambda(*, func_name: str = None, payload: typing.Mapping[str, str] = None):
    if func_name is None:
        raise Exception('ERROR: functionName parameter cannot be NULL')
    payload_str = json.dumps(payload)
    payload_bytes_arr = bytes(payload_str, encoding='utf8')
    client = boto3.client('lambda')
    resp = client.invoke(
        FunctionName=func_name,
        InvocationType="RequestResponse",
        Payload=payload_bytes_arr
    )
    return resp


def getData(keyword, query_date):
    index = "articles"
    # Note that certain fields are boosted (^).
    query = {
        "size": 5,
        'query': {
            "bool": {
                "must": [
                    {
                        "range": {
                            "date": {
                                "gte": query_date
                            }
                        }
                    },
                    {
                        "multi_match": {
                            "query": keyword,
                            "fields": ["text", "title", "tags^2"]
                        }
                    }
                ]
            }
        }
    }

    result = requests.get(url, auth=awsauth, headers=headers,
                          data=json.dumps(query)).json()
    # print(result)

    return result

    print('Request completed ...')
    print(r)
    print(r.text)
