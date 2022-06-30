import boto3
import json
import flair
import base64

from os.path import join
from flair.models import SequenceTagger
from flair.tokenization import Sentence
from pathlib import Path

flair.cache_root = Path("/mnt/model-cache/.flair")
s3 = boto3.client('s3')


def handler(event, context):
    try:
        data = json.loads(base64.b64decode(event['Records'][0]['kinesis']['data']))
        text = data['text']
        id_str = data['id_str']

        tagger = SequenceTagger.load("flair/ner-english-large")
        sentence = Sentence(text)
        tagger.predict(sentence)
        count = 0
        for label in sentence.get_labels('ner'):
            prediction = dict(
                value=label.value,
                score=label.score,
                entity=label.data_point.text,
                id_str=id_str)

            encoded_data = json.dumps(prediction).encode('utf-8')
            print(encoded_data)

            file_key = join('ner', f'{id_str}-{count}.json')
            bucket = 'YOUR_BUCKET_NAME'  # PredictionBucketName
            s3.put_object(Body=encoded_data, Bucket=bucket, Key=file_key)
            count += 1
    except Exception as e:
        print(repr(e))
