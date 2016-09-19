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
            log_date=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
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

    def test_match_with_log_date_not_visit_date(self):

        # Setup: create a rating event that occurred within a task
        create_location_event(
            log_date=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            visit_date=datetime.datetime(9000, 1, 1, 1, 0, 0, 0),
            event_type="Rating: 1",
            url="http://url1.com",
            user_id=0,
        )
        create_location_event(
            log_date=datetime.datetime(9000, 1, 1, 1, 0, 0, 0),
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            event_type="Rating: 1",
            url="http://url2.com",
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
        self.assertEqual(ratings.first().url, "http://url1.com")

    def test_dont_make_rating_for_non_rating_event(self):

        create_location_event(
            log_date=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
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
            log_date=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
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
            log_date=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
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
            log_date=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
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

    def test_skip_ratings_that_couldnt_be_classified(self):

        # The first and last events don't fall into a valid task period
        create_location_event(
            log_date=datetime.datetime(2000, 1, 1, 11, 0, 0, 0),
            event_type="Rating: 0",
            url="http://url1.com",
            user_id=0,
        )
        create_location_event(
            log_date=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            event_type="Rating: 1",
            url="http://url2.com",
            user_id=0,
        )
        create_location_event(
            log_date=datetime.datetime(2000, 1, 1, 13, 0, 0, 0),
            event_type="Rating: 2",
            url="http://url2.com",
            user_id=0,
        )

        create_task_period(
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
            user_id=0,
        )

        compute_location_ratings()
        ratings = LocationRating.select()
        self.assertEqual(ratings.count(), 1)
        self.assertEqual(ratings.first().rating, 1)

    def test_return_ratings_that_couldnt_be_classified(self):

        # The first and last events don't fall into a valid task period
        unmatched_rating_0 = create_location_event(
            log_date=datetime.datetime(2000, 1, 1, 11, 0, 0, 0),
            event_type="Rating: 0",
            url="http://url1.com",
            user_id=0,
        )
        create_location_event(
            log_date=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            event_type="Rating: 1",
            url="http://url2.com",
            user_id=0,
        )
        unmatched_rating_1 = create_location_event(
            log_date=datetime.datetime(2000, 1, 1, 13, 0, 0, 0),
            event_type="Rating: 2",
            url="http://url2.com",
            user_id=0,
        )

        create_task_period(
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
            user_id=0,
        )

        unclassified = compute_location_ratings()
        self.assertIn({'user_id': 0, 'event_id': unmatched_rating_0.id}, unclassified)
        self.assertIn({'user_id': 0, 'event_id': unmatched_rating_1.id}, unclassified)

    def test_hand_label_rating_events(self):

        # This rating event isn't aligned with the task period below (it comes after).
        # But we will still be able to associate it with that task created because
        # with a list of hand labels that we pass in.
        rating_event = create_location_event(
            log_date=datetime.datetime(2000, 1, 1, 12, 3, 0, 0),
            event_type="Rating: 1",
            url="http://url2.com",
            user_id=2,
        )
        create_task_period(
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
            user_id=2,
            task_index=4,
        )

        compute_location_ratings(labels=[
            {'user_id': 2, 'task_index': 4, 'event_id': rating_event.id},
        ])
        self.assertEqual(LocationRating.select().count(), 1)
        rating = LocationRating.select().first()
        self.assertEqual(rating.task_index, 4)
        self.assertEqual(rating.hand_aligned, True)
