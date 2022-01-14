# -*- coding: utf-8 -*-

from task_specs import ImageClassificationTask, ImageSegmentationTask
from pipeline import TaskSequence
import json
import toloka.client as toloka

# Read the credentials
with open('creds.json') as cred_f:

    creds = json.loads(cred_f.read())
    tclient = toloka.TolokaClient(creds['token'], creds['mode'])

exam = ImageClassificationTask(configuration='text_exam.yaml', client=tclient)

main = ImageClassificationTask(configuration='text_detect.yaml', client=tclient)

outline = ImageSegmentationTask(configuration='text_outline.yaml', client=tclient)

y = TaskSequence(sequence=[exam, main, outline], client=tclient)

y.start()

exit()
