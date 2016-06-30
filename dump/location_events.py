#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging

from dump import dump_csv
from models import LocationEvent


logger = logging.getLogger('data')


@dump_csv(__name__, [
    "Id", "User", "Visit Date", "Log Date", "Title", "URL", "Event type", "Tab ID"])
def main(*args, **kwargs):

    for event in LocationEvent.select():
        yield [[
            event.id,
            event.user_id,
            event.visit_date,
            event.log_date,
            event.title,
            event.url,
            event.event_type,
            event.tab_id,
        ]]

    raise StopIteration


def configure_parser(parser):
    parser.description = "Dump records of all browser events."
