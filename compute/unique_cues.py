#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn
import json

from models import UniqueCue


logger = logging.getLogger('data')


def compute_unique_cues(cues):

    # Create a new index for this computation
    last_compute_index = UniqueCue.select(fn.Max(UniqueCue.compute_index)).scalar() or 0
    compute_index = last_compute_index + 1

    # Get the distinct participant IDs and concern indexes
    participant_ids = set([cue['participant_id'] for cue in cues])

    # Go through every concern for every participant.  Find the number of URLs
    # they visited that no one else visited.
    for participant_id in participant_ids:

        participant_cues = filter(lambda cue: cue['participant_id'] == participant_id, cues)
        participant_cue_names = [cue['cue'] for cue in participant_cues]

        others_cues = filter(lambda cue: cue['participant_id'] != participant_id, cues)
        others_cue_names = [cue['cue'] for cue in others_cues]

        # Compute the URLs that this participant visited uniquely, and that they share with others
        unique_participant_cue_names = set(participant_cue_names) - set(others_cue_names)
        shared_participant_cue_names =\
            set(participant_cue_names) - set(unique_participant_cue_names)

        # Save all cues that the participant visited to the database, including
        # whether they visited them uniquely.
        for cue_name in unique_participant_cue_names:
            UniqueCue.create(
                compute_index=compute_index,
                participant_id=participant_id,
                cue=cue_name,
                unique=True,
            )

        for cue_name in shared_participant_cue_names:
            UniqueCue.create(
                compute_index=compute_index,
                participant_id=participant_id,
                cue=cue_name,
                unique=False,
            )


def main(cues_json_filename, *args, **kwargs):

    # Load a list of all of the cues that participants mentioned
    with open(cues_json_filename) as cues_file:
        cues = json.load(cues_file)

    compute_unique_cues(cues)


def configure_parser(parser):
    parser.description = "Compute whether each cue each participant mentioned was unique or not."
    parser.add_argument(
        "cues_json_filename",
        help=(
            "Name of a JSON file containing an array with one dictionary for " +
            "each mention of a cue:  " +
            "{\"participant_id\": <id>, \"cue\": \"<cue_name>\"}",
        )
    )
