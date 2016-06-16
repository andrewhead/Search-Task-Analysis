#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging

from dump import dump_csv
from models import Postquestionnaire


logger = logging.getLogger('data')


@dump_csv(__name__, ["User", "Rank", "Concern"])
def main(*args, **kwargs):

    for questionnaire in Postquestionnaire.select():
        yield [
            [questionnaire.user_id, 1, questionnaire.concern_rank1],
            [questionnaire.user_id, 2, questionnaire.concern_rank2],
            [questionnaire.user_id, 3, questionnaire.concern_rank3],
            [questionnaire.user_id, 4, questionnaire.concern_rank4],
            [questionnaire.user_id, 5, questionnaire.concern_rank5],
            [questionnaire.user_id, 6, questionnaire.concern_rank6],
        ]

    raise StopIteration


def configure_parser(parser):
    parser.description = "Dump participants' rankings of support-related concerns."
