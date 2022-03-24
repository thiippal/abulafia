# -*- coding: utf-8 -*-

import json
import toloka.client as toloka
import sys
sys.path.append('..')

from actions import Forward
from task_specs import TaskSequence, ImageClassification


# Read the credentials
with open('../creds.json') as cred_f:

    creds = json.loads(cred_f.read())
    tclient = toloka.TolokaClient(creds['token'], creds['mode'])

detect = ImageClassification(configuration='tasks/test_forward.yaml', client=tclient)
pool_1 = ImageClassification(configuration='tasks/pool1.yaml', client=tclient)
pool_2 = ImageClassification(configuration='tasks/pool2.yaml', client=tclient)
forward = Forward(configuration='tasks/forward.yaml', client=tclient, targets=[pool_1, pool_2])

y = TaskSequence(sequence=[detect, forward, pool_1, pool_2], client=tclient)

y.start()
