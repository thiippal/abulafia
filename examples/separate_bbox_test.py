# -*- coding: utf-8 -*-

import json
import toloka.client as toloka
import sys
sys.path.append('..')

from actions import SeparateBBoxes
from task_specs import TaskSequence, SegmentationClassification, AddOutlines, LabelledSegmentationVerification


# Read the credentials
with open('../creds.json') as cred_f:

    creds = json.loads(cred_f.read())
    tclient = toloka.TolokaClient(creds['token'], creds['mode'])

classify = SegmentationClassification(configuration="tasks/detect_target.yaml", client=tclient)
separate_bboxes = SeparateBBoxes(target=classify, configuration="tasks/separate_bboxes.yaml", add_labels=True)
outline_targets = AddOutlines(configuration="tasks/outline_targets.yaml", client=tclient)

pipeline = TaskSequence(sequence=[separate_bboxes, classify, outline_targets], client=tclient)

pipeline.start()
