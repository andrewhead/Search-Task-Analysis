#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging

from dump import dump_csv
from models import Prequestionnaire


logger = logging.getLogger('data')


@dump_csv(__name__, [
    "User", "Years Programming", "Years Programming with Python",
    "Years Programming Professionally", "Reason to Write Code",
    "Programming Proficiency", "Python Proficiency", "Occupation",
    "Occupation (Other)", "Gender",
])
def main(*args, **kwargs):

    for questionnaire in Prequestionnaire.select():
        yield [[
            questionnaire.user_id,
            questionnaire.programming_years,
            questionnaire.python_years,
            questionnaire.professional_years,
            questionnaire.coding_reason,
            questionnaire.programming_proficiency,
            questionnaire.python_proficiency,
            questionnaire.occupation,
            questionnaire.occupation_other,
            questionnaire.gender,
        ]]

    raise StopIteration


def configure_parser(parser):
    parser.description = "Dump participants' prequestionnaire answers."
