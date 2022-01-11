# -*- coding: utf-8 -*-

from tasks import ImageClassificationTask, InputData
import json
import toloka.client as toloka


# Read the credentials
with open('creds.json') as cred_f:

    creds = json.loads(cred_f.read())
    tclient = toloka.TolokaClient(creds['token'], creds['mode'])


input_data = InputData('data/exam.tsv')
pipe = ImageClassificationTask(configuration='exam.json', client=tclient)(input_data)

