# -*- coding: utf-8 -*-

from task_specs import ImageClassification
from pipeline import TaskSequence
import json
import toloka.client as toloka

# Read Toloka credentials from file
with open('creds.json') as cred_f:

    creds = json.loads(cred_f.read())
    tclient = toloka.TolokaClient(creds['token'], creds['mode'])

# Create an ImageClassification task with training and exam
exam = ImageClassification(configuration='tasks/text_exam.yaml', client=tclient)

# Create a task sequence object
seq = TaskSequence(sequence=[exam], client=tclient)

# Start the pipeline
seq.start()
