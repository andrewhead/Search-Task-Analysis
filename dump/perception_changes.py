#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging

from dump import dump_csv
from models import Postquestionnaire


logger = logging.getLogger('data')


@dump_csv(__name__, ["User", "Perception change"])
def main(*args, **kwargs):

    for postquestionnaire in Postquestionnaire.select():
        yield [[postquestionnaire.user_id, postquestionnaire.likert_perception_change]]

    raise StopIteration


def configure_parser(parser):
    parser.description = "Dump records of all user ratings of how their perceptions changed."
