#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging

from compute.task_periods import _get_concern_index
from dump import dump_csv
from models import Question


logger = logging.getLogger('data')


@dump_csv(__name__, ["User", "Question Index", "Concern Index", "Concern", "Confidence"])
def main(*args, **kwargs):

    for question in Question.select():
        concern_index = _get_concern_index(question.user_id, question.question_index)
        yield [[
            question.user_id,
            question.question_index,
            concern_index,
            question.concern,
            question.likert_confidence,
        ]]

    raise StopIteration


def configure_parser(parser):
    parser.description = "Dump records of all participants' ratings of confidence on questions."
