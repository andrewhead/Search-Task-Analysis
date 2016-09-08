#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn
from urlparse import urlparse
import json

from dump import dump_csv
from _urls import standardize_url
from models import LocationVisit


logger = logging.getLogger('data')
PILOT_MAX_USER_ID = 4


@dump_csv(__name__, [
    "Compute Index", "User", "Task Index", "Concern Index", "Tab ID", "URL",
    "Unique URL", "Domain", "Path", "Fragment", "Query", "Page Type",
    "Page Title", "Start Time", "End Time", "Time passed (s)"],
    delimiter='|')
def main(page_types_json_filename, *args, **kwargs):

    with open(page_types_json_filename) as page_types_file:
        page_types = json.load(page_types_file)

    # Only dump the most recently computed location visits (ignore all others).
    latest_compute_index = LocationVisit.select(fn.Max(LocationVisit.compute_index)).scalar()
    visits = (
        LocationVisit
        .select()
        .where(
            LocationVisit.compute_index == latest_compute_index,
        )
    )

    # Store a list of URLs for which labels are missing
    urls_without_labels = set()

    for visit in visits:

        # Split URL into the constituent parts that can be used
        # to uniquely identify this URL in relation to others.
        # Note that while the same URL with different query strings may refer to the same
        # page, this isn't always true.  Take the forum PHP script for Panda3D as an example.
        # The same is true with fragments, specifically for Google Groups, where fragments
        # are used to select different groups and topics.
        url_parsed = urlparse(visit.url)
        path = url_parsed.path
        fragment = url_parsed.fragment
        query = url_parsed.query
        domain = url_parsed.netloc.lstrip("www.")

        # Fetch semantic labels for this URL
        # Store missing URLs for non-pilot study participants.
        # Currently, it's not important for us to be able to classify URLs for pilot participants.
        unique_url = standardize_url(visit.url)
        if unique_url not in page_types:
            if visit.user_id > PILOT_MAX_USER_ID:
                urls_without_labels.add(unique_url)
        else:
            page_type = page_types[unique_url]['main_type']

        time_passed = visit.end - visit.start
        seconds = time_passed.seconds + (time_passed.microseconds / float(1000000))

        yield [[
            visit.compute_index,
            visit.user_id,
            visit.task_index,
            visit.concern_index,
            visit.tab_id,
            visit.url,
            unique_url,
            domain,
            path,
            fragment,
            query,
            page_type,
            visit.title,
            visit.start,
            visit.end,
            seconds,
        ]]

    # Print out a list of URLs for which labels were not found
    for url in sorted(urls_without_labels):
        logger.debug("No label found for URL: %s", url)

    raise StopIteration


def configure_parser(parser):
    parser.description = "Dump most recently computed records of user visits to URLs."
    parser.add_argument(
        "page_types_json_filename",
        help=(
            "Name of a JSON file that maps URLs to file types.  " +
            "The format of each row should be:\n" +
            "\"<url>\": {\"main_type\": \"<main type>\", \"types\": " +
            "[<list of all relevant types>]}"
        )
    )
