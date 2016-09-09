#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import datetime

from compute.navigation_ngrams import compute_navigation_ngrams
from tests.base import TestCase
from tests.modelfactory import create_location_visit
from models import LocationVisit, NavigationNgram


logger = logging.getLogger('data')
PAGE_TYPE_LOOKUP = {
    "page1": {"main_type": "page_type_1", "redirect": False},
    "page2": {"main_type": "page_type_2", "redirect": False},
    "redirect": {"main_type": "redirect", "redirect": True},
}


class ComputeLocationVisitsTest(TestCase):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(
            [LocationVisit, NavigationNgram],
            *args, **kwargs
        )

    def test_compute_bigrams_from_location_sequence(self):

        # Create a set of visits that a participant made to a few pages
        create_location_visit(
            user_id=3,
            concern_index=2,
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
        )
        create_location_visit(
            user_id=3,
            concern_index=2,
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 3, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 4, 0),
        )
        create_location_visit(
            user_id=3,
            concern_index=2,
            url="page2",
            start=datetime.datetime(2000, 1, 1, 12, 0, 5, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 6, 0),
        )

        # Run a routine to compute all n-grams of page visits of a given length
        compute_navigation_ngrams(length=2, page_type_lookup=PAGE_TYPE_LOOKUP)
        ngram_models = NavigationNgram.select()

        # Two ngrams should have been created from a sequence of 3 visits
        self.assertEqual(ngram_models.count(), 2)

        # Make sure that all of the left-to-right subsequences can be found
        ngrams = [n.ngram for n in ngram_models]
        self.assertIn("page_type_1, page_type_1", ngrams)
        self.assertIn("page_type_1, page_type_2", ngrams)

        # Make sure the participant's ID, ngram length, and task's concern index are stored
        ngram_model = ngram_models.first()
        self.assertEqual(ngram_model.length, 2)
        self.assertEqual(ngram_model.user_id, 3)
        self.assertEqual(ngram_model.concern_index, 2)

    def test_compute_ngrams_within_participant(self):

        create_location_visit(
            user_id=3,
            concern_index=1,
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
        )
        create_location_visit(
            user_id=3,
            concern_index=1,
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 3, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 4, 0),
        )
        # This third visit is by another participant, and shouldn't be connected
        # to the past visits as an n-gram
        create_location_visit(
            user_id=4,
            concern_index=1,
            url="page2",
            start=datetime.datetime(2000, 1, 1, 12, 0, 5, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 6, 0),
        )

        compute_navigation_ngrams(length=2, page_type_lookup=PAGE_TYPE_LOOKUP)
        ngram_models = NavigationNgram.select()
        self.assertEqual(ngram_models.count(), 1)

    def test_compute_ngrams_within_concern(self):

        create_location_visit(
            user_id=3,
            concern_index=1,
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
        )
        create_location_visit(
            user_id=3,
            concern_index=1,
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 3, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 4, 0),
        )
        # This third visit is for a different task than the first two.  It shouldn't be connected
        # to the past visits as an n-gram
        create_location_visit(
            user_id=3,
            concern_index=2,
            url="page2",
            start=datetime.datetime(2000, 1, 1, 12, 0, 5, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 6, 0),
        )

        compute_navigation_ngrams(length=2, page_type_lookup=PAGE_TYPE_LOOKUP)
        ngram_models = NavigationNgram.select()
        self.assertEqual(ngram_models.count(), 1)

    def test_skip_pages_that_appear_to_be_redirects(self):

        create_location_visit(
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
        )
        # In the page lookup dictionary, this entry will have a "redirect" flag that's
        # set to true.  It should be skipped in the ngrams.
        create_location_visit(
            url="redirect",
            start=datetime.datetime(2000, 1, 1, 12, 0, 3, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 4, 0),
        )
        create_location_visit(
            url="page2",
            start=datetime.datetime(2000, 1, 1, 12, 0, 5, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 6, 0),
        )

        compute_navigation_ngrams(length=2, page_type_lookup=PAGE_TYPE_LOOKUP)
        ngram_models = NavigationNgram.select()
        self.assertEqual(ngram_models.count(), 1)
        ngram = ngram_models.first()
        self.assertEqual(ngram.ngram, "page_type_1, page_type_2")
