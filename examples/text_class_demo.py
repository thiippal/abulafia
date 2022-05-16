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

# Create an ImageSegmentation task using the configuration file
classify = TextClassification(configuration='tasks/text_classification.yaml', client=tclient)

# Add the task into a TaskSequence
sequence = TaskSequence(sequence=[classify], client=tclient)

# Start the sequence; create tasks on Toloka
sequence.start()
