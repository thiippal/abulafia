# -*- coding: utf-8 -*-

import json
import toloka.client as toloka
import sys
sys.path.append('..')

from actions import Verify
from task_specs import ImageSegmentation, SegmentationVerification, TaskSequence


# Read the credentials
with open('../creds.json') as cred_f:

    creds = json.loads(cred_f.read())
    tclient = toloka.TolokaClient(creds['token'], creds['mode'])

outline = ImageSegmentation(configuration='tasks/text_outline_2.yaml', client=tclient)
verify = SegmentationVerification(configuration='tasks/verify.yaml', client=tclient)
process = Verify(task=verify, configuration='tasks/process.yaml')

y = TaskSequence(sequence=[outline, verify, process], client=tclient)

y.start()
