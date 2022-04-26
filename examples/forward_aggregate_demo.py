# -*- coding: utf-8 -*-

import json
import toloka.client as toloka
import sys
sys.path.append('..')

from actions import Forward, Aggregate
from task_specs import ImageSegmentation, TaskSequence, MulticlassVerification, ImageClassification, FixImageSegmentation


# Read the credentials
with open('../creds.json') as cred_f:

    creds = json.loads(cred_f.read())
    tclient = toloka.TolokaClient(creds['token'], creds['mode'])

detect = ImageClassification(configuration="tasks/text_detect.yaml", client=tclient)
outline = ImageSegmentation(configuration="tasks/text_outline_forward.yaml", client=tclient)
forward_bool = Forward(configuration="tasks/forward_bool.yaml", client=tclient, targets=[outline])
aggregate_detect = Aggregate(configuration="tasks/aggregate_detect.yaml", task=detect, forward=forward_bool)
verify_outlines = MulticlassVerification(configuration="tasks/verify_multiclass.yaml", client=tclient)
fix_outlines = FixImageSegmentation(configuration="tasks/fix_outlines.yaml", client=tclient)
forward_str = Forward(configuration="tasks/forward_multiclass.yaml", client=tclient, targets=[fix_outlines])
aggregate_verify = Aggregate(configuration="tasks/aggregate_verify.yaml", task=verify_outlines, forward=forward_str)

y = TaskSequence(sequence=[detect, aggregate_detect, forward_bool, outline, verify_outlines, aggregate_verify,
                           forward_str, fix_outlines], client=tclient)

y.start()
