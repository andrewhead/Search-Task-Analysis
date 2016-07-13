#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn

from dump import dump_csv
from _urls import get_label
from models import LocationRating


logger = logging.getLogger('data')


@dump_csv(__name__, [
    "Compute Index", "User", "Task Index", "Concern Index", "URL", "Domain", "Page Type",
    "Search Target", "Created by Project Developers", "Rating", "Page Title", "Visit Date"])
def main(*args, **kwargs):

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

        label = get_label(rating.url)
        domain = label['domain'] if label is not None else "Unclassified"
        page_type = label['name'] if label is not None else "Unclassified"
        search_target = label.get('target') if label is not None else None
        created_by_project_developers = label['project'] if label is not None else None

        if label is None:
            urls_without_labels.add(rating.url)

        yield [[
            rating.compute_index,
            rating.user_id,
            rating.task_index,
            rating.concern_index,
            rating.url,
            domain,
            page_type,
            search_target,
            created_by_project_developers,
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
