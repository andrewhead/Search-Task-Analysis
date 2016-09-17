#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn
import json

from dump._urls import standardize_url
from models import LocationVisit, UniqueUrl


logger = logging.getLogger('data')


def compute_unique_urls(page_type_lookup, exclude_users=None):

    exclude_users = [] if exclude_users is None else exclude_users

    # Create a new index for this computation
    last_compute_index = UniqueUrl.select(fn.Max(UniqueUrl.compute_index)).scalar() or 0
    compute_index = last_compute_index + 1

    # Fetch the set of visits for the most recently computed visits
    visit_compute_index = LocationVisit.select(fn.Max(LocationVisit.compute_index)).scalar()
    visits = LocationVisit.select().where(
        LocationVisit.compute_index == visit_compute_index,
        LocationVisit.user_id.not_in(exclude_users),
    )

    # Get the distinct participant IDs and concern indexes
    participant_ids = set([visit.user_id for visit in visits])

    # Go through every concern for every participant.  Find the number of URLs
    # they visited that no one else visited.
    for participant_id in participant_ids:

        participant_concern_visits = visits.where(LocationVisit.user_id == participant_id)
        others_visits = visits.where(LocationVisit.user_id != participant_id)

        # Create a list of unique URLs that this participant visited
        participant_urls = [visit.url for visit in participant_concern_visits]
        participant_standardized_urls = [standardize_url(url) for url in participant_urls]

        # Create a list of unique URLs that all others visited
        others_urls = [visit.url for visit in others_visits]
        others_standardized_urls = [standardize_url(url) for url in others_urls]

        # Compute the URLs that this participant visited uniquely, and that they share with others
        unique_participant_urls = set(participant_standardized_urls) - set(others_standardized_urls)
        shared_participant_urls = set(participant_standardized_urls) - set(unique_participant_urls)

        # Save all URLs that the participant visited to the database, including
        # whether they visited them uniquely.
        for url in unique_participant_urls:
            UniqueUrl.create(
                compute_index=compute_index,
                user_id=participant_id,
                url=url,
                unique=True,
            )

        for url in shared_participant_urls:
            UniqueUrl.create(
                compute_index=compute_index,
                user_id=participant_id,
                url=url,
                unique=False,
            )


def main(page_types_json_filename, exclude_users, *args, **kwargs):

    # Load a dictionary that describes the page types for URLs visited
    with open(page_types_json_filename) as page_types_file:
        page_type_lookup = json.load(page_types_file)

    compute_unique_urls(page_type_lookup, exclude_users)


def configure_parser(parser):
    parser.description = "Compute whether each URL each participant visited was unique or not."
    parser.add_argument(
        "page_types_json_filename",
        help=(
            "Name of a JSON file that maps URLs to file types.  " +
            "The format of each row should be:" +
            "\"<url>\": {\"main_type\": \"<main type>\", \"types\": " +
            "[<list of all relevant types>]}"
        )
    )
    parser.add_argument(
        "--exclude-users",
        default=[1, 2, 3, 4],
        nargs='+',
        type=int,
        help="The IDs of participants to exclude from this analysis(default: %(default)s)",
    )
