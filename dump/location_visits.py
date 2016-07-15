#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn

from dump import dump_csv
from _urls import get_label
from models import LocationVisit


logger = logging.getLogger('data')


@dump_csv(__name__, [
    "Compute Index", "User", "Task Index", "Concern Index", "Tab ID", "URL",
    "Domain", "Page Type", "Search Target", "Created by Project Developers",
    "Page Title", "Start Time", "End Time", "Time passed (s)"],
    delimiter='|')
def main(*args, **kwargs):

    # Only dump the most recently computed location visits (ignore all others).
    latest_compute_index = LocationVisit.select(fn.Max(LocationVisit.compute_index)).scalar()
    visits = (
        LocationVisit
        .select()
        .where(
            LocationVisit.compute_index == latest_compute_index
        )
    )

    # Store a list of URLs for which labels are missing
    urls_without_labels = set()

    for visit in visits:

        label = get_label(visit.url)
        domain = label['domain'] if label is not None else "Unclassified"
        page_type = label['name'] if label is not None else "Unclassified"
        search_target = label.get('target') if label is not None else None
        created_by_project_developers = label['project'] if label is not None else None

        if label is None:
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
