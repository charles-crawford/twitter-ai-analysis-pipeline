import boto3
import json
import re
import time
import os
import sys

from os.path import join
from datetime import datetime as dt
from tweepy import OAuthHandler
from tweepy import API
from tweepy import Stream

kinesis = boto3.client('kinesis')
secrets_manager = boto3.client('secretsmanager')
s3 = boto3.client('s3')

CONSUMER_KEY = secrets_manager.get_secret_value(SecretId='TwitterConsumerKey')['SecretString']
CONSUMER_SECRET = secrets_manager.get_secret_value(SecretId='TwitterConsumerSecret')['SecretString']
ACCESS_TOKEN = secrets_manager.get_secret_value(SecretId='TwitterAccessToken')['SecretString']
ACCESS_TOKEN_SECRET = secrets_manager.get_secret_value(SecretId='TwitterAccessTokenSecret')['SecretString']
#
# CONSUMER_KEY = os.environ['CONSUMER_KEY']
# CONSUMER_SECRET = os.environ['CONSUMER_SECRET']
# ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
# ACCESS_TOKEN_SECRET = os.environ['ACCESS_TOKEN_SECRET']

auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = API(auth, wait_on_rate_limit=True)


def clean(raw):
    result = re.sub("<[a][^>]*>(.+?)</[a]>", 'Link.', raw)
    result = re.sub('&gt;', "", result)
    result = re.sub('&#x27;', "'", result)
    result = re.sub('&quot;', '"', result)
    result = re.sub('&#x2F;', ' ', result)
    result = re.sub('<p>', ' ', result)
    result = re.sub('</i>', '', result)
    result = re.sub('&#62;', '', result)
    result = re.sub('<i>', ' ', result)
    result = re.sub("\n", '', result)
    result = re.sub('@[\w]+', '', result)
    result = re.sub('RT :', '', result)
    result = re.sub(r'http\S+', '', result)
    return result


def process_date(date_str):
    return dict(day=dt.strptime(date_str, '%a %b %d %H:%M:%S +0000 %Y').date().day,
                month=dt.strptime(date_str, '%a %b %d %H:%M:%S +0000 %Y').date().month,
                year=dt.strptime(date_str, '%a %b %d %H:%M:%S +0000 %Y').date().year)


def process_status(status):
    try:
        status = status._json
        status_keys = status.keys()
        if 'extended_tweet' in status_keys:
            full_text = status['extended_tweet']['full_text']
        elif 'retweeted_status' in status_keys and 'extended_tweet' in status['retweeted_status']:
            full_text = status['retweeted_status']['extended_tweet']['full_text']
        else:
            full_text = status['text']

        mentions = []
        if status['entities']['user_mentions']:
            for mention in status['entities']['user_mentions']:
                mentions.append(mention['screen_name'])

        # Athena does not like empty arrays, so set to None
        if len(mentions) == 0:
            mentions = None

        date_str = status['created_at']
        id_str = status['id_str']
        data = dict(
            text=clean(full_text),
            created_at=date_str,
            id_str=id_str,
            favorite_count=status['favorite_count'],
            retweet_count=status['retweet_count'],
            followers_count=status['user']['followers_count'],
            mentions=mentions,
            location=status['user']['location'],
            user=status['user']['screen_name'],
            geo=status['geo']
        )

        data.update(process_date(date_str))
        print(data)
        encoded_data = json.dumps(data).encode('utf-8')

        file_key = join('tweets', f'{id_str}.json')
        bucket = 'ml-prediction-bucket-e07adba6-ae1c-43e4-8148-4ead73d60834'
        s3.put_object(Body=encoded_data, Bucket=bucket, Key=file_key)

        response = kinesis.put_record(
            Data=encoded_data,
            StreamName='data-ingest-stream',
            PartitionKey='tweets'
        )
        print(response)
    except Exception as e:
        print('error', repr(e))


class TwitterStreamListener(Stream):
    def __init__(self, time_limit=300):
        self.start_time = time.time()
        self.time_limit = time_limit
        super(TwitterStreamListener, self).__init__(CONSUMER_KEY,
                                                    CONSUMER_SECRET,
                                                    ACCESS_TOKEN,
                                                    ACCESS_TOKEN_SECRET)

    def on_status(self, status):
        elapsed_time = time.time() - self.start_time
        if elapsed_time < self.time_limit:
            process_status(status)
            return True
        else:
            return False


def handler(event, context):
    stream = TwitterStreamListener()
    stream.filter(track=['insurrection'], languages=['en'])
