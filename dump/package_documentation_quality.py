#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging

from dump import dump_csv
from models import PackageComparison, PackagePair


logger = logging.getLogger('data')


@dump_csv(__name__, ["User", "Stage", "Comparison Rating", "Package 1", "Package 2"])
def main(*args, **kwargs):

    # See the note on formulating this query in `dump/package_comparisons.py`
    comparisons = (
        PackageComparison
        .select(
            PackageComparison.user_id,
            PackageComparison.stage,
            PackageComparison.likert_quality_documentation,
            PackagePair.package1,
            PackagePair.package2,
        )
        .join(PackagePair, on=(PackageComparison.user_id == PackagePair.user_id))
        .naive()
    )

    for comparison in comparisons:
        yield [[
            comparison.user_id,
            comparison.stage,
            comparison.likert_quality_documentation,
            comparison.package1,
            comparison.package2,
        ]]

    raise StopIteration


def configure_parser(parser):
    parser.description = "Dump participants' ratings comparing packages' documentation quality."
