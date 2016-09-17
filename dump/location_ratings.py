#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn
from urlparse import urlparse
import json

from dump import dump_csv
from _urls import standardize_url
from models import LocationRating


logger = logging.getLogger('data')
PILOT_MAX_USER_ID = 4


@dump_csv(__name__, [
    "Compute Index", "User", "Task Index", "Concern Index", "URL", "Domain", "Page Type",
    "Rating", "Page Title", "Visit Date"])
def main(page_types_json_filename, *args, **kwargs):

    with open(page_types_json_filename) as page_types_file:
        page_types = json.load(page_types_file)

    # Only dump the most recently computed location ratings (ignore all others).
    latest_compute_index = LocationRating.select(fn.Max(LocationRating.compute_index)).scalar()
    ratings = (
        LocationRating
        .select()
        .where(
            LocationRating.compute_index == latest_compute_index
        )
    )

    # Store a list of URLs for which labels are missing
    urls_without_labels = set()

    for rating in ratings:

        # Get the domain name of where this rating happened
        url_parsed = urlparse(rating.url)
        domain = url_parsed.netloc.lstrip("www.")

        # Fetch semantic labels for this URL
        # Store missing URLs for non-pilot study participants.
        # Currently, it's not important for us to be able to classify URLs for pilot participants.
        unique_url = standardize_url(rating.url)
        if unique_url not in page_types:
            if rating.user_id > PILOT_MAX_USER_ID:
                urls_without_labels.add(unique_url)
        else:
            page_type = page_types[unique_url]['main_type']

        yield [[
            rating.compute_index,
            rating.user_id,
            rating.task_index,
            rating.concern_index,
            rating.url,
            domain,
            page_type,
            rating.rating,
            rating.title,
            rating.visit_date,
        ]]

    # Print out a list of URLs for which labels were not found
    for url in sorted(urls_without_labels):
        logger.debug("No label found for URL: %s", url)

    raise StopIteration


def configure_parser(parser):
    parser.description = "Dump most recently computed record of all user ratings of web pages."
    parser.add_argument(
        "page_types_json_filename",
        help=(
            "Name of a JSON file that maps URLs to file types.  " +
            "The format of each row should be:" +
            "\"<url>\": {\"main_type\": \"<main type>\", \"types\": " +
            "[<list of all relevant types>]}"
        )
    )
