#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging

from dump import dump_csv
from models import Question, Postquestionnaire, PackageComparison


logger = logging.getLogger('data')


# This single script stores the "N/A" answers for all ordinal questions.
# This is because we can easily filter down to a specific question with the
# "Question" column, and it keeps us from writing a dozen dump scripts
# that will all have nearly equivalent logic.
@dump_csv(__name__, ["User", "Question", "N/A"])
def main(*args, **kwargs):

    for question in Question.select():
        comparison_title = "Task " + str(question.question_index) + " package comparison"
        confidence_title = "Task " + str(question.question_index) + " confidence"
        yield [
            [question.user_id, comparison_title, question.na_likert_comparison_evidence],
            [question.user_id, confidence_title, question.na_likert_confidence],
        ]

    for comparison in PackageComparison.select():
        yield [
            [comparison.user_id, "Preference " + comparison.stage, comparison.na_likert_preference],
            [comparison.user_id, "Quality " + comparison.stage, comparison.na_likert_quality],
        ]

    for postquestionnaire in Postquestionnaire.select():
        yield [
            [postquestionnaire.user_id, "Perception Change",
                postquestionnaire.na_likert_perception_change]
        ]

    raise StopIteration


def configure_parser(parser):
    parser.description = "Dump records of participants' N/A responses."
