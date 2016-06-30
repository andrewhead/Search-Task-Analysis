#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import datetime

from compute.location_ratings import compute_location_ratings
from tests.base import TestCase
from tests.modelfactory import create_task_period, create_location_event
from models import LocationEvent, TaskPeriod, LocationRating


logger = logging.getLogger('data')


class ComputeLocationRatingTest(TestCase):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(
            [LocationEvent, TaskPeriod, LocationRating],
            *args, **kwargs
        )

    def test_extract_location_rating(self):

        # Setup: create a rating event that occurred within a task
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            event_type="Rating: 1",
            url="http://url1.com",
            user_id=0,
        )
        create_task_period(
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
            task_index=3,
            concern_index=5,
            user_id=0,
        )

        # Test: a rating should be created for the URL visited with
        # the index of the task and concern of the task period that was taking place at the time.
        compute_location_ratings()
        ratings = LocationRating.select()
        self.assertEqual(ratings.count(), 1)
        rating = ratings[0]
        self.assertEqual(rating.user_id, 0)
        self.assertEqual(rating.task_index, 3)
        self.assertEqual(rating.concern_index, 5)
        self.assertEqual(rating.visit_date, datetime.datetime(2000, 1, 1, 12, 0, 1, 0))
        self.assertEqual(rating.url, "http://url1.com")

    def test_dont_make_rating_for_non_rating_event(self):

        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            event_type="Tab opened",  # this event is not a rating and shouldn't be read as one
            url="http://url1.com",
        )
        create_task_period(
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
            task_index=3,
            concern_index=5,
        )
        compute_location_ratings()
        self.assertEqual(LocationRating.select().count(), 0)

    def test_location_event_must_match_task_period_and_user_id(self):

        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            event_type="Rating: 0",
            url="http://url1.com",
            user_id=0,
        )
        # For the task periods below, the `task_index` parameter serves no function,
        # except to vary between all periods so that we know which task the rating
        # is associated with after it has been extracted.
        # This task is a mismatch because it's for the wrong user.
        create_task_period(
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
            task_index=2,
            user_id=1,
        )
        # This task is a match, with the right timing and the right user.
        create_task_period(
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
            task_index=3,
            user_id=0,
        )
        # This task is a mismatch, with the wrong timing but the right user.
        create_task_period(
            start=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 4, 0, 0),
            task_index=4,
            user_id=0,
        )

        compute_location_ratings()
        ratings = LocationRating.select()
        self.assertEqual(ratings.count(), 1)
        rating = ratings[0]
        self.assertEqual(rating.user_id, 0)
        self.assertEqual(rating.task_index, 3)

    def test_by_default_associate_rating_with_latest_computed_task_periods(self):

        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            event_type="Rating: 0",
            url="http://url1.com",
            user_id=0,
        )

        # All three of these tasks have the same (matching) periods.
        # But the second one was the latest one to be computed (compute_index=2)
        create_task_period(
            compute_index=0,
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
            task_index=1,
        )
        create_task_period(
            compute_index=2,
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
            task_index=2,
        )
        create_task_period(
            compute_index=1,
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
            task_index=3,
        )

        compute_location_ratings()
        rating = LocationRating.select()[0]
        self.assertEqual(rating.task_index, 2)

    def test_if_task_compute_index_specified_only_match_tasks_with_that_index(self):

        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            event_type="Rating: 0",
            url="http://url1.com",
            user_id=0,
        )

        create_task_period(
            compute_index=0,
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
            task_index=1,
        )
        create_task_period(
            compute_index=2,
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
            task_index=2,
        )
        create_task_period(
            compute_index=1,
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
            task_index=3,
        )

        compute_location_ratings(task_compute_index=1)
        rating = LocationRating.select()[0]
        self.assertEqual(rating.task_index, 3)
