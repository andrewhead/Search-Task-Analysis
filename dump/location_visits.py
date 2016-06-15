#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging

from dump import dump_csv
from models import LocationVisit


logger = logging.getLogger('data')


@dump_csv(__name__, [
    "Compute Index", "User", "Task Index", "Concern Index",
    "URL", "Page Title", "Start Time", "End Time"])
def main(*args, **kwargs):

    for visit in LocationVisit.select():
        yield [[
            visit.compute_index,
            visit.user_id,
            visit.task_index,
            visit.concern_index,
            visit.url,
            visit.title,
            visit.start,
            visit.end,
        ]]

    raise StopIteration


def configure_parser(parser):
    parser.description = "Dump records of all user visits to locations on the web."
