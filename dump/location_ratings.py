#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging

from dump import dump_csv
from _urls import get_domain_name
from models import LocationRating


logger = logging.getLogger('data')


@dump_csv(__name__, [
    "Compute Index", "User", "Task Index", "Concern Index",
    "URL", "Domain", "Rating", "Page Title", "Visit Date"])
def main(*args, **kwargs):

    for rating in LocationRating.select():
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
    parser.description = "Dump records of all user ratings of web pages."
