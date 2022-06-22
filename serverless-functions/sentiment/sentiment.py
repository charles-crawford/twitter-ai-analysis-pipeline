import boto3
import json
import base64
import traceback

from os.path import join
from transformers import AutoModelForSequenceClassification
from transformers import AutoTokenizer, AutoConfig
import numpy as np
from scipy.special import softmax


def handler(event, context):
    try:
        s3 = boto3.client('s3')
        data = json.loads(base64.b64decode(event['Records'][0]['kinesis']['data']))
        text = data['text']
        id_str = data['id_str']

        MODEL = f"cardiffnlp/twitter-roberta-base-sentiment-latest"
        tokenizer = AutoTokenizer.from_pretrained(MODEL)
        config = AutoConfig.from_pretrained(MODEL)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL)

        encoded_input = tokenizer(text, return_tensors='pt')
        output = model(**encoded_input)
        scores = output[0][0].detach().numpy()
        scores = softmax(scores)

        prediction = {}
        ranking = np.argsort(scores)
        ranking = ranking[::-1]
        for i in range(scores.shape[0]):
            l = config.id2label[ranking[i]]
            s = float(scores[ranking[i]])
            prediction[l.lower()] = s

        prediction['sentiment'] = max(prediction, key=prediction.get)
        prediction['confidence'] = prediction[prediction['sentiment']]
        prediction['id_str'] = id_str
        encoded_data = json.dumps(prediction).encode('utf-8')
        print(encoded_data)
        file_key = join('sentiment', f'{id_str}.json')
        bucket = 'ml-prediction-bucket-e07adba6-ae1c-43e4-8148-4ead73d60834'
        s3.put_object(Body=encoded_data, Bucket=bucket, Key=file_key)

    except Exception as e:
        print(repr(e))
        print(traceback.format_exc())
