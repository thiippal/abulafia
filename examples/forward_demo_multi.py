# -*- coding: utf-8 -*-

import json
from pydoc import cli
import toloka.client as toloka
import sys
sys.path.append('..')

from actions import Forward
from task_specs import ImageSegmentation, TaskSequence, MulticlassVerification, ImageClassification, FixImageSegmentation


# Read the credentials
with open('../creds.json') as cred_f:

    creds = json.loads(cred_f.read())
    tclient = toloka.TolokaClient(creds['token'], creds['mode'])

detect = ImageClassification(configuration="tasks/text_detect.yaml", client=tclient)
outline = ImageSegmentation(configuration="tasks/text_outline_forward.yaml", client=tclient)
forward_bool = Forward(configuration="tasks/forward_bool.yaml", client=tclient, targets=[outline])
verify_outlines = MulticlassVerification(configuration="tasks/verify_multiclass.yaml", client=tclient)
fix_outlines = FixImageSegmentation(configuration="tasks/fix_outlines.yaml", client=tclient)
forward_str = Forward(configuration="tasks/forward_multiclass.yaml", client=tclient, targets=[fix_outlines])

y = TaskSequence(sequence=[detect, forward_bool, outline, verify_outlines, forward_str, fix_outlines], client=tclient)

y.start()
