# -*- coding: utf-8 -*-

import json
import toloka.client as toloka
import sys
sys.path.append('..')

from actions import Forward
from task_specs import TaskSequence, FixImageSegmentation


# Read the credentials
with open('../creds.json') as cred_f:

    creds = json.loads(cred_f.read())
    tclient = toloka.TolokaClient(creds['token'], creds['mode'])

fix = FixImageSegmentation(configuration='tasks/fix_outlines.yaml', client=tclient)

y = TaskSequence(sequence=[fix], client=tclient)

y.start()
