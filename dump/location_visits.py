#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn
from urlparse import urlparse

from dump import dump_csv
from _urls import get_label
from models import LocationVisit


logger = logging.getLogger('data')
PILOT_MAX_USER_ID = 4


@dump_csv(__name__, [
    "Compute Index", "User", "Task Index", "Concern Index", "Tab ID", "URL",
    "Domain", "Path", "Fragment", "Query", "Page Type", "Search Target",
    "Created by Project Developers", "Page Title", "Start Time", "End Time", "Time passed (s)"],
    delimiter='|')
def main(*args, **kwargs):

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

        # Fetch semantic labels for this URL
        label = get_label(visit.url)
        domain = label['domain'] if label is not None else "Unclassified"
        page_type = label['name'] if label is not None else "Unclassified"
        search_target = label.get('target') if label is not None else None
        created_by_project_developers = label['project'] if label is not None else None

        # Store missing URLs for non-pilot study participants.
        # Currently, it's not important for us to be able to classify URLs for pilot participants.
        if label is None and visit.user_id > PILOT_MAX_USER_ID:
            urls_without_labels.add(visit.url)

        time_passed = visit.end - visit.start
        seconds = time_passed.seconds + (time_passed.microseconds / float(1000000))

        yield [[
            visit.compute_index,
            visit.user_id,
            visit.task_index,
            visit.concern_index,
            visit.tab_id,
            visit.url,
            domain,
            path,
            fragment,
            query,
            page_type,
            search_target,
            created_by_project_developers,
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
