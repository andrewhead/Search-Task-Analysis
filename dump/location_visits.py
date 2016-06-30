#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn

from dump import dump_csv
from _urls import get_domain_name
from models import LocationVisit


logger = logging.getLogger('data')


@dump_csv(__name__, [
    "Compute Index", "User", "Task Index", "Concern Index", "Tab ID",
    "URL", "Domain", "Page Title", "Start Time", "End Time"])
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

    for visit in visits:
        yield [[
            visit.compute_index,
            visit.user_id,
            visit.task_index,
            visit.concern_index,
            visit.tab_id,
            visit.url,
            get_domain_name(visit.url),
            visit.title,
            visit.start,
            visit.end,
        ]]

    raise StopIteration


def configure_parser(parser):
    parser.description = "Dump most recently computed records of user visits to URLs."
