#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn
import json
from nltk.util import ngrams as nltk_compute_ngrams

from dump._urls import standardize_url
from models import LocationVisit, NavigationNgram


logger = logging.getLogger('data')


def compute_navigation_ngrams(length, page_type_lookup):
    '''
    Compute n-grams of sequences of pages visited, of a certain length.
    A `page_type_lookup` dictionary must be provided, that maps URLs to their page types.
    '''
    # Create a new index for this computation
    last_compute_index = NavigationNgram.select(fn.Max(NavigationNgram.compute_index)).scalar() or 0
    compute_index = last_compute_index + 1

    # Fetch the set of visits for the most recently computed visits
    visit_compute_index = LocationVisit.select(fn.Max(LocationVisit.compute_index)).scalar()
    visits = LocationVisit.select().where(LocationVisit.compute_index == visit_compute_index)

    # Get the distinct participant IDs and concern indexes
    participant_ids = set([visit.user_id for visit in visits])
    concern_indexes = set([visit.concern_index for visit in visits])

    # Go through every concern for every participant.  For each page they visit,
    # increment the visits to a vertex.  For each transition from one page to the next,
    # increment the occurrence of a transition between two page types.
    for participant_id in participant_ids:
        for concern_index in concern_indexes:

            participant_concern_visits = visits.where(
                LocationVisit.user_id == participant_id,
                LocationVisit.concern_index == concern_index,
            ).order_by(LocationVisit.start.asc())

            # Create a list of unique URLs that each participant visited
            urls = [visit.url for visit in participant_concern_visits]
            standardized_urls = [standardize_url(url) for url in urls]

            # Create a list of all page types visited.
            # If this is a redirect, then skip it.  For all intents and purposes,
            # someone is traveling between two the page type before and after it.
            page_types = []
            for url in standardized_urls:
                if url in page_type_lookup:
                    url_info = page_type_lookup[url]
                    if not url_info['redirect']:
                        page_types.append(url_info['main_type'])
                else:
                    logger.warn("URL %s not in page type lookup.  Giving it 'Unknown' type", url)
                    page_types.append("Unknown")

            # Compute n-grams using NLTK command
            ngrams = nltk_compute_ngrams(page_types, length)

            # Save each n-gram to the database
            for ngram_tuple in ngrams:
                NavigationNgram.create(
                    compute_index=compute_index,
                    user_id=participant_id,
                    concern_index=concern_index,
                    length=length,
                    ngram=", ".join(ngram_tuple),
                )


def main(page_types_json_filename, min_length, max_length, *args, **kwargs):

    # Load a dictionary that describes the page types for URLs visited
    with open(page_types_json_filename) as page_types_file:
        page_type_lookup = json.load(page_types_file)

    # Compute n-grams for all requested lengths of n-gram
    for length in range(min_length, max_length + 1):
        compute_navigation_ngrams(length, page_type_lookup)


def configure_parser(parser):
    parser.description = "Compute n-grams of page types that participants visited in sequence."
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
        "--min-length",
        default=2,
        help="The minimum length of ngram to extract (default: %(default)s)",
    )
    parser.add_argument(
        "--max-length",
        help="The maximum length of ngram to extract (default: %(default)s)",
        default=6,
    )
