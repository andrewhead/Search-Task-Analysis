#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging

from compute.task_periods import _get_concern_index
from dump import dump_csv
from models import Strategy, Question, PackagePair


logger = logging.getLogger('data')
CONCERNS_SHORTHAND = [
    "How-To docs",
    "answer rate",
    "doc recency",
    "welcoming community",
    "developer trustworthiness",
    "users' backgrounds",
]

# The column names here are specifically designed so
# that this data can be imported into MAXQDA
column_names = ["Document Group", "Document Name", "$Package 1", "$Package 2"]
for concern in CONCERNS_SHORTHAND:
    column_names.append("Strategy for assessing " + concern)
for concern in CONCERNS_SHORTHAND:
    column_names.append("Evidence of " + concern)


@dump_csv(__name__, column_names, delimiter='|')
def main(*args, **kwargs):

    # Fetch distinct user IDs from the question data
    user_ids = [
        question.user_id for question in
        Question.select(Question.user_id).group_by(Question.user_id)
    ]

    # Yield a record of all participant responses for each participant
    for user_id in user_ids:

        # Build a new blank record for this participant that we can index by concern index.
        user_record = {
            'strategies': ["No response." for _ in range(len(CONCERNS_SHORTHAND))],
            'evidence': ["No response." for _ in range(len(CONCERNS_SHORTHAND))],
        }

        # Fetch a reference to the pair of packages that the participant used
        package_pair = PackagePair.select().where(PackagePair.user_id == user_id).first()

        # Save all of the "evidence" question responses, in concern order
        for question in Question.select().where(Question.user_id == user_id):
            concern_index = _get_concern_index(user_id, question.question_index)
            user_record['evidence'][concern_index] = question.evidence

        # Save all of the "strategy" question responses, in concern order
        for strategy in Strategy.select().where(Strategy.user_id == user_id):
            concern_index = _get_concern_index(user_id, strategy.question_index)
            user_record['strategies'][concern_index] = strategy.strategy

        # Assemble and return a single row of a CSV file for the user
        response_list = [
            "Search study responses",
            "Participant " + str(user_id),
            package_pair.package1,
            package_pair.package2,
        ]
        response_list.extend(user_record['strategies'])
        response_list.extend(user_record['evidence'])
        yield [response_list]

    raise StopIteration


def configure_parser(parser):
    parser.description = "Dump participants' open-ended responses."
