# -*- coding: utf-8 -*-

import sys
sys.path.append('..')

from task_specs import TaskSequence, TextClassification
import json
import toloka.client as toloka

# Read the credentials from the JSON file
with open('../creds.json') as cred_f:

    creds = json.loads(cred_f.read())
    tclient = toloka.TolokaClient(creds['token'], creds['mode'])

# Create a TextClassification exam using the configuration file
classify_text_exam = TextClassification(configuration='config/classify_text_exam.yaml', client=tclient)

# Create a TextClassification task using the configuration file
classify_text = TextClassification(configuration='config/classify_text.yaml', client=tclient)

# Add the task into a TaskSequence
sequence = TaskSequence(sequence=[classify_text_exam, classify_text], client=tclient)

# Start the sequence; create tasks on Toloka
sequence.start()
