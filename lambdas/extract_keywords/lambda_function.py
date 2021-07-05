# import relevant packages
# from newspaper import Article
from nltk.tokenize import sent_tokenize, word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
import re
import pandas as pd
import numpy as np
import datetime
import glob
import unicodedata
from datetime import timedelta, date
from io import BytesIO
import zipfile
import os
import boto3
import json
from fuzzywuzzy import fuzz

#load nltk data from s3 into lambda tmp folder
s3 = boto3.resource('s3')
bucket_name = 'edmscraperbucket'
KEY = 'keyword_extraction/nltk_data.zip'
#zip_obj = s3.get_obj(Bucket=bucket_name, Key=KEY)
local_file_name = '/tmp/nltk_data.zip'
s3.Bucket(bucket_name).download_file(KEY, local_file_name)

with zipfile.ZipFile(local_file_name, 'r') as zip_ref:
    zip_ref.extractall('/tmp/')
print(os.path.isfile('/tmp/nltk_data/copora/stopwords/english'))

#only import nltk after loading the data
import nltk
nltk.data.path.append("/tmp/nltk_data")
from nltk.corpus import stopwords
from nltk import pos_tag
import extract_keywords

#get the default stopwords
stopwords = set(stopwords.words('english'))


#add extra stopwords to remove date, unwanted verbs and adjectives which cannot be removed by postagging
stop_words = stopwords
extra_stopwords = ['shares', 'person', 'useful', 'govtech', 'cio', 'yonhap', 'size', 'tackle', 'right', 'day', 'tried', 'tested', 'make', 'sure', 'used', 'help', 'yesterday', 'today', 'tomorrow', 'percent', 'per', 'cent', 'could', 'many', 'add', 'use', 'need', 'goods', 'million', 'thousand', 'company', 'retailers', 'saw', 'see', 'new', 'like', 'today', 'tomorrow', 'guide',
                   'people', 'want', 'yet', 'way', 'time', 'back', 'whether', 'if', 'yes', 'older', 'noted', 'went', 'told', 'tell', 'younger', 'another', 'worth', 'noting', 'well', 'called', 'named', 'never', 'lee', 'quah', 'ong', 'ng', 'lim', 'tan', 'shared', 'says', 'say', 'said', 'cio', 'cios', 'month', 'top', 'world', 'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'january', 'february', 'march', 'april', 'may', 'june', 'july',
                   'august', 'september', 'october', 'november', 'december', 'month', 'months', 'years', 'year', 'near', 'also', 'would', 'able']
for word in extra_stopwords:
    stop_words.add(word)


def lambda_handler(event, context):
    # Get the service resource.
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Articles')

    # get the keywords count from dynamodb
    keywords_table = dynamodb.Table('edm_keywords')
    response = keywords_table.scan()
    data = response['Items']

    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])
    articles_date = {x['date']: x for x in data}

    s3 = boto3.client('s3')
    # get the keyword list
    obj = s3.get_object(Bucket=bucket_name, Key='new_keywords.json')
    keyword_list = set(json.loads(obj['Body'].read()))

    obj2 = s3.get_object(Bucket=bucket_name, Key='keywords.json')
    keyword_list2 = set(json.loads(obj2['Body'].read()))

    keyword_list.update(keyword_list2)

    for record in event['Records']:
        item = record['dynamodb']['NewImage']
        print(item)
    # for item in data:
        if 'tags' not in item.keys():
            item['tags'] = None
        #add the keywords to those articles without tags
        if 'NULL' in item['tags'] and item['text']['S'] != None and len(item['text']['S']) > 50:
            item['tags_new'] = extract_keywords.extract_single_text_ngram(
                item['text']['S'], list(set(keyword_list)), topn=10)
            #inset into dynamodb table
            table.put_item(Item={'date': item['date'].get('S'),
                                 'url': item['url'].get('S'),
                                 'text': item['text'].get('S'),
                                 'blurp': item['blurp'].get('S'),
                                 'imgurl': item['imgurl'].get('S'),
                                 'title': item['title'].get('S'),
                                 'tags': item['tags'],
                                 'tags_new': item['tags_new'],
                                 'category': item['category'].get('S')})
        #for those with tags use tags instead
        elif 'S' in item['tags']:
            item['tags_new'] = item['tags'].get('S')
            tags = item['tags'].get('S')
            tags = tags.split(', ')
            for tag in tags:
                if tags != ' ':
                    keyword_list.add(tag.lower())
            table.put_item(Item={'date': item['date'].get('S'),
                                 'url': item['url'].get('S'),
                                 'text': item['text'].get('S'),
                                 'blurp': item['blurp'].get('S'),
                                 'imgurl': item['imgurl'].get('S'),
                                 'title': item['title'].get('S'),
                                 'tags': item['tags'].get('S'),
                                 'tags_new': item['tags_new'],
                                 'category': item['category'].get('S')})

        # ignore those with 'M' (require cleaning)
        try:
            date = item['date'].get('S')
        except:
            pass

        # if its none, initialse item
        if articles_date.get(date) is None:
            articles_date[date] = {
                'date': date,
                'keywords_count': {},
                'articles': set()
            }
        print(articles_date)
        print(item)
        # check if title has been added to the set in articles date to avoid adding the same article twice
        if item['title'].get('S') is not None and item['title'].get('S') not in articles_date[date]['articles']:
            # get item in your db based on article published date update keyword_count for given date
            articles_date[date]['keywords_count'] = extract_keywords.add_keywords(
                item['tags_new'], articles_date[date]['keywords_count'])
            # update set of articles based on date
            articles_date[date]['articles'].add(item['title']['S'])
            print(articles_date[date])
            keywords_table.put_item(Item=articles_date[date])

    # 1. if tags inside your item
    # 2. get item in your db based on article published date
    # 3. if its none, initialse item
    # 4. check if title already in item
    # 5. if not update your item with keywords
    # 6. Save item back to db

    print(keyword_list)

    # save the complete list of keywords to s3
    s3 = boto3.resource('s3')
    file_name = 'keywords.json'
    object = s3.Object(bucket_name, file_name)
    object.put(
        Body=(bytes(json.dumps(list(set(keyword_list)), indent=2).encode('UTF-8'))))

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
