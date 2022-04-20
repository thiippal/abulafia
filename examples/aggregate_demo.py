# -*- coding: utf-8 -*-

import json
import toloka.client as toloka
import sys
sys.path.append('..')

from actions import Aggregate, Forward
from task_specs import TaskSequence, ImageClassification


# Read the credentials
with open('../creds.json') as cred_f:

    creds = json.loads(cred_f.read())
    tclient = toloka.TolokaClient(creds['token'], creds['mode'])

detect = ImageClassification(configuration='tasks/test_forward.yaml', client=tclient)
pool_1 = ImageClassification(configuration='tasks/pool1.yaml', client=tclient)
pool_2 = ImageClassification(configuration='tasks/pool2.yaml', client=tclient)
forward_agg = Forward(configuration='tasks/forward_agg.yaml', client=tclient, targets=[pool_1, pool_2])
aggregate = Aggregate(configuration="tasks/aggregate.yaml", task=detect, forward=forward_agg)

y = TaskSequence(sequence=[detect, aggregate, forward_agg, pool_1, pool_2], client=tclient)

y.start()
