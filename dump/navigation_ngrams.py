#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging

from dump import dump_csv
from models import NavigationNgram


logger = logging.getLogger('data')


@dump_csv(__name__, ["Compute Index", "User", "Concern Index", "Length", "Ngram"])
def main(*args, **kwargs):

    for ngram in NavigationNgram.select():
        yield [[
            ngram.compute_index,
            ngram.user_id,
            ngram.concern_index,
            ngram.length,
            ngram.ngram,
        ]]

    raise StopIteration


def configure_parser(parser):
    parser.description = "Dump records of all n-grams of page sequences visited."
