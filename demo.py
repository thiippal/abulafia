# -*- coding: utf-8 -*-

from tasks import ImageClassificationTask
import json
import toloka.client as toloka


# Read the credentials
with open('creds.json') as cred_f:

    creds = json.loads(cred_f.read())
    tclient = toloka.TolokaClient(creds['token'], creds['mode'])

t = ImageClassificationTask(configuration='conf.json', client=tclient)
