#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn

from dump import dump_csv
from _urls import get_domain_name
from models import LocationRating


logger = logging.getLogger('data')


@dump_csv(__name__, [
    "Compute Index", "User", "Task Index", "Concern Index",
    "URL", "Domain", "Rating", "Page Title", "Visit Date"])
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

    for rating in ratings:
        yield [[
            rating.compute_index,
            rating.user_id,
            rating.task_index,
            rating.concern_index,
            rating.url,
            get_domain_name(rating.url),
            rating.rating,
            rating.title,
            rating.visit_date,
        ]]

    raise StopIteration


def configure_parser(parser):
    parser.description = "Dump most recently computed record of all user ratings of web pages."
