# -*- coding: utf-8 -*-

from abulafia.actions import Forward, Aggregate, SeparateBBoxes
from abulafia.task_specs import TaskSequence, ImageClassification, ImageSegmentation, SegmentationClassification
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

# Create class instances of all CrowdsourcingTasks and Actions in the pipeline

# Binary image classification task for identifying possible text in diagrams
detect_text = ImageClassification(configuration="config/detect_text.yaml", client=tclient)

# Image segmentation task asking the worker to outline text elements from diagrams
outline_text = ImageSegmentation(configuration="config/outline_text.yaml", client=tclient)

# Forward action that forwards all tasks with output "True" from the detect_text pool to outline_text pool
forward_detect = Forward(configuration="config/forward_detect.yaml", client=tclient, targets=[outline_text])

# Aggregate action that determines the most probable correct outputs for the detect_text pool. Aggregated 
# tasks are then forwarded with the forward_detect action defined above.
aggregate_detect = Aggregate(configuration="config/aggregate_detect.yaml", task=detect_text, forward=forward_detect)

# Verification task asking the workers to determine if image segmentations from pool outline_text are done correctly
verify_outlines = SegmentationClassification(configuration="config/verify_outlines.yaml", client=tclient)

# Pool where partially correct image segmentations go from forwarding
fix_outlines = ImageSegmentation(configuration="config/fix_outlines.yaml", client=tclient)

# Binary segmentation classification task where workers identify potential targets for the outlined text elements
has_target = SegmentationClassification(configuration="config/detect_target.yaml", client=tclient)

# SeparateBBoxes action to separate bounding boxes from the pool outline_text and create new tasks to pool has_target
separate_bboxes = SeparateBBoxes(configuration="config/separate_bboxes.yaml", target=has_target, add_label="source")

# Forward action to forward outline_text pool results based on the results from the verification pool verify_outlines.
# Tasks are either forwarded to be corrected by another worker, rejected, or accepted and forwarded to the action
# separate_bboxes.
forward_verify = Forward(configuration="config/forward_verify.yaml", client=tclient, targets=[fix_outlines,
                                                                                              separate_bboxes])

# Aggregate action to determine most probable correct answers to the verificatoin task verify_outlines.
# After aggregation, tasks are forwarded with forward_verify.
aggregate_verify = Aggregate(configuration="config/aggregate_verify.yaml", task=verify_outlines, forward=forward_verify)

# Combine the tasks and actions into one pipeline
pipe = TaskSequence(sequence=[detect_text, aggregate_detect, forward_detect, outline_text, verify_outlines,
                              aggregate_verify, forward_verify, fix_outlines, separate_bboxes, has_target],
                    client=tclient)

# Start the task sequence; create the tasks on Toloka
pipe.start()
