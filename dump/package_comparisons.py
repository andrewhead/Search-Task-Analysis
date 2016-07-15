#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging

from compute.task_periods import _get_concern_index
from dump import dump_csv
from models import Question, PackagePair


logger = logging.getLogger('data')


def _standardize_package_name(package_name):
    stripped = package_name.strip()
    lower_case = stripped.lower()
    return lower_case


@dump_csv(__name__, [
    "User", "Question Index", "Concern Index",
    "Comparison Rating", "Package 1", "Package 2"
])
def main(*args, **kwargs):

    # Join the questions table on the packagepair table so that
    # we have access to the names of the packages that the
    # participant was comparing.
    # Thanks to 'TehTechGuy', we know to specify the "select" fields and
    # to also chain on a call to the "naive" function in order to make
    # sure that the joined fields are added to the returned objects:
    # http://stackoverflow.com/questions/19366023/python-peewee-select-from-multiple-tables
    questions = (
        Question
        .select(
            Question.user_id,
            Question.question_index,
            Question.likert_comparison_evidence,
            PackagePair.package1,
            PackagePair.package2,
        )
        .join(PackagePair, on=(Question.user_id == PackagePair.user_id))
        .naive()
    )

    for question in questions:
        concern_index = _get_concern_index(question.user_id, question.question_index)
        yield [[
            question.user_id,
            question.question_index,
            concern_index,
            question.likert_comparison_evidence,
            _standardize_package_name(question.package1),
            _standardize_package_name(question.package2),
        ]]

    raise StopIteration


def configure_parser(parser):
    parser.description = "Dump records of all participants' ratings comparing packages."
