#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import datetime

from compute.unique_urls import compute_unique_urls
from tests.base import TestCase
from tests.modelfactory import create_location_visit
from models import LocationVisit, UniqueUrl


logger = logging.getLogger('data')
PAGE_TYPE_LOOKUP = {
    "page1": {"main_type": "page_type_1", "redirect": False},
    "page2": {"main_type": "page_type_2", "redirect": False},
    "redirect": {"main_type": "redirect", "redirect": True},
}


class ComputeLocationVisitsTest(TestCase):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(
            [LocationVisit, UniqueUrl],
            *args, **kwargs
        )

    def test_url_shared_between_two_users_isnt_unique_for_either(self):

        # Create visits where two participants visited the same page
        create_location_visit(
            user_id=3,
            concern_index=2,
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
        )
        create_location_visit(
            user_id=4,
            concern_index=2,
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 5, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 6, 0),
        )

        # Run a routine to compute whether each URL is unique for each participant
        compute_unique_urls(page_type_lookup=PAGE_TYPE_LOOKUP)
        unique_urls = UniqueUrl.select()

        # Two unique URL records should have been created: one for each participant for each URL
        self.assertEqual(unique_urls.count(), 2)
        records = [(u.user_id, u.url, u.unique) for u in unique_urls]
        self.assertIn((3, "page1", False), records)
        self.assertIn((4, "page1", False), records)

    def test_only_one_record_appears_per_participant_and_url(self):

        # Create visits where one participant visited the same URL twice
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
            start=datetime.datetime(2000, 1, 1, 12, 0, 5, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 6, 0),
        )

        compute_unique_urls(page_type_lookup=PAGE_TYPE_LOOKUP)
        unique_urls = UniqueUrl.select()
        self.assertEqual(unique_urls.count(), 1)
        records = [(u.user_id, u.url, u.unique) for u in unique_urls]
        self.assertIn((3, "page1", True), records)

    def test_url_that_no_one_else_has_visited_is_unique(self):

        create_location_visit(
            user_id=3,
            concern_index=2,
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
        )
        # In this visit, participant 3 goes to a URL that participant 4 hadn't.
        create_location_visit(
            user_id=3,
            concern_index=2,
            url="page2",
            start=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
        )
        create_location_visit(
            user_id=4,
            concern_index=2,
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 5, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 6, 0),
        )

        compute_unique_urls(page_type_lookup=PAGE_TYPE_LOOKUP)
        unique_urls = UniqueUrl.select()
        self.assertEqual(unique_urls.count(), 3)
        records = [(u.user_id, u.url, u.unique) for u in unique_urls]
        self.assertIn((3, "page1", False), records)
        self.assertIn((3, "page2", True), records)
        self.assertIn((4, "page1", False), records)

    def test_ignore_participants_with_excluded_user_ids(self):

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
            start=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
        )
        create_location_visit(
            user_id=4,
            concern_index=2,
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 5, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 6, 0),
        )

        compute_unique_urls(page_type_lookup=PAGE_TYPE_LOOKUP, exclude_users=[2, 3])
        unique_urls = UniqueUrl.select()
        self.assertEqual(unique_urls.count(), 1)
        records = [(u.user_id, u.url, u.unique) for u in unique_urls]
        self.assertIn((4, "page1", True), records)
