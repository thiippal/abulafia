# -*- coding: utf-8 -*-

from abulafia.task_specs import TaskSequence, TextClassification
import argparse
import json
import toloka.client as toloka

# Set up the argument parser
ap = argparse.ArgumentParser()

# Add argument for input
ap.add_argument("-c", "--creds", required=True,
                help="Path to a JSON file that contains Toloka credentials. "
                     "The file should have two keys: 'token' and 'mode'. "
                     "The key 'token' should contain the Toloka API key, whereas "
                     "the key 'mode' should have the value 'PRODUCTION' or 'SANDBOX' "
                     "that defines the environment in which the pipeline should be run.")

# Parse the arguments
args = vars(ap.parse_args())

# Assign arguments to variables
cred_file = args['creds']

# Read the credentials from the JSON file
with open(cred_file) as cred_f:

    creds = json.loads(cred_f.read())
    tclient = toloka.TolokaClient(creds['token'], creds['mode'])

# Create a TextClassification task using the configuration file
classify_text = TextClassification(configuration='config/classify_text_gold.yaml', client=tclient)

# Add the tasks into a TaskSequence
pipe = TaskSequence(sequence=[classify_text], client=tclient)

# Start the task sequence; create tasks on Toloka
pipe.start()
