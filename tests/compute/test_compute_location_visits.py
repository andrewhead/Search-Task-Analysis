#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import datetime

from compute.location_visits import compute_location_visits
from tests.base import TestCase
from tests.modelfactory import create_task_period, create_location_event
from models import LocationEvent, TaskPeriod, LocationVisit


logger = logging.getLogger('data')


class ComputeLocationVisitsTest(TestCase):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(
            [LocationEvent, TaskPeriod, LocationVisit],
            *args, **kwargs
        )

    def test_create_location_visit(self):

        # Setup: create two location events bounding a single visit
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            event_type="Tab activated",
            url="http://url1.com"
        )
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
            event_type="Tab deactivated",
            url="http://url1.com"
        )
        create_task_period(
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
            task_index=3,
            concern_index=5,
        )

        # Test: make sure a 'visit' is created for a URL that is visited and then left,
        # that inherits the time bounds defined by entering and exiting the URL, and that includes
        # the index of the task and concern of the task period that was taking place at that time.
        compute_location_visits()
        visits = LocationVisit.select()
        self.assertEqual(visits.count(), 1)
        visit = visits[0]
        self.assertEqual(visit.user_id, 0)
        self.assertEqual(visit.task_index, 3)
        self.assertEqual(visit.concern_index, 5)
        self.assertEqual(visit.start, datetime.datetime(2000, 1, 1, 12, 0, 1, 0))
        self.assertEqual(visit.end, datetime.datetime(2000, 1, 1, 12, 0, 2, 0))
        self.assertEqual(visit.url, "http://url1.com")

    def test_associate_location_visit_with_task_period_it_occured_within(self):

        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            event_type="Tab activated",
            url="http://url1.com"
        )
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 6, 0),
            event_type="Tab deactivated",
            url="http://url1.com"
        )
        create_task_period(
            start=datetime.datetime(2000, 1, 1, 11, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 11, 59, 0, 0),
            task_index=1,
        )
        create_task_period(
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
            task_index=2,
        )
        create_task_period(
            start=datetime.datetime(2000, 1, 1, 12, 3, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 4, 0, 0),
            task_index=3,
        )

        compute_location_visits()
        visit = LocationVisit.select()[0]
        self.assertEqual(visit.task_index, 2)

    def test_make_no_location_visit_if_it_doesnt_start_after_or_end_before_end_of_task(self):

        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 11, 59, 1, 0),
            event_type="Tab activated",
            url="http://url1.com"
        )
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 1, 0, 0),
            event_type="Tab deactivated",
            url="http://url1.com"
        )
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 3, 0, 0),
            event_type="Tab activated",
            url="http://url2.com"
        )
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 3, 0, 0),
            event_type="Tab deactivated",
            url="http://url2.com"
        )
        create_task_period(
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
        )

        self.assertEqual(LocationVisit.select().count(), 0)

    def test_make_location_visit_associated_with_tasks_of_same_user(self):

        create_location_event(
            user_id=0,
            visit_date=datetime.datetime(2000, 1, 1, 11, 0, 1, 0),
            event_type="Tab activated",
            url="http://url1.com"
        )
        create_location_event(
            user_id=0,
            visit_date=datetime.datetime(2000, 1, 1, 11, 0, 2, 0),
            event_type="Tab deactivated",
            url="http://url1.com"
        )
        create_task_period(
            user_id=1,
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
        )

        self.assertEqual(LocationVisit.select().count(), 0)

    def test_chain_multiple_location_visits(self):

        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            event_type="Tab activated",
            url="http://url1.com",
            tab_id=1,
        )
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
            event_type="Tab deactivated",
            url="http://url1.com",
            tab_id=1,
        )
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
            event_type="Tab activated",
            url="http://url2.com",
            tab_id=2,
        )
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 5, 0),
            event_type="Tab deactivated",
            url="http://url2.com",
            tab_id=2,
        )
        create_task_period(
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
            task_index=3,
            concern_index=5,
        )

        compute_location_visits()
        visits = LocationVisit.select()
        self.assertEqual(visits.count(), 2)
        urls = [visit.url for visit in LocationVisit.select()]
        self.assertIn("http://url1.com", urls)
        self.assertIn("http://url2.com", urls)

    def test_acceptable_activating_location_events(self):

        time = datetime.datetime(2000, 1, 1, 12, 0, 1, 0)
        create_task_period(
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
        )

        for activating_event_type in [
                "Tab opened",
                "Tab content loaded (pageshow)",
                "Tab activated",
                "Window activated",
                ]:
            create_location_event(
                visit_date=time,
                event_type=activating_event_type,
            )
            time += datetime.timedelta(seconds=1)
            create_location_event(
                visit_date=time,
                event_type="Window deactivated",  # deactivating event type
            )
            time += datetime.timedelta(seconds=1)

        compute_location_visits()
        self.assertEqual(LocationVisit.select().count(), 4)

    def test_acceptable_deactivating_location_events(self):

        time = datetime.datetime(2000, 1, 1, 12, 0, 1, 0)

        # For every user ID we could foresee having for this test, create a record of
        # of a task being completed for this user.
        for user_id in range(0, 10):
            create_task_period(
                start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
                end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
                user_id=user_id,
            )

        # We vary the user ID with each iteration to start fresh, so that
        # every user has just one activating event and just one deactivating
        # event (in other words, just one visit).
        for user_id, deactivating_event_type in enumerate([
                "Tab closed",
                "Tab deactivated",
                "Window deactivated",
                ]):
            create_location_event(
                user_id=user_id,
                visit_date=time,
                event_type="Tab activated",  # activating event type
            )
            time += datetime.timedelta(seconds=1)
            create_location_event(
                user_id=user_id,
                visit_date=time,
                event_type=deactivating_event_type,
            )
            time += datetime.timedelta(seconds=1)

        compute_location_visits()
        self.assertEqual(LocationVisit.select().count(), 3)

    def test_end_location_visit_when_another_page_loaded(self):

        time = datetime.datetime(2000, 1, 1, 12, 0, 1, 0)

        # For every user ID we could foresee having for this test, create a record of
        # of a task being completed for this user.
        for user_id in range(0, 10):
            create_task_period(
                start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
                end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
                user_id=user_id,
            )

        # We vary the user ID with each iteration to start fresh, so that
        # every user has just one activating event and just one deactivating
        # event (in other words, just one visit).
        for user_id, deactivating_event_type in enumerate([
                "Tab content loaded (ready)",
                "Tab content loaded (load)",
                "Tab content loaded (pageshow)",
                ]):
            create_location_event(
                user_id=user_id,
                visit_date=time,
                event_type="Tab activated",  # activating event type
                url="http://url1.com",
            )
            time += datetime.timedelta(seconds=1)
            create_location_event(
                user_id=user_id,
                visit_date=time,
                event_type=deactivating_event_type,
                url="http://url2.com",
            )
            time += datetime.timedelta(seconds=1)

        compute_location_visits()
        self.assertEqual(LocationVisit.select().count(), 3)

    def test_dont_end_location_visit_when_a_page_is_reloaded(self):

        time = datetime.datetime(2000, 1, 1, 12, 0, 1, 0)

        # For every user ID we could foresee having for this test, create a record of
        # of a task being completed for this user.
        for user_id in range(0, 10):
            create_task_period(
                start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
                end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
                user_id=user_id,
            )

        # We vary the user ID with each iteration to start fresh, so that
        # every user has just one activating event and just one deactivating
        # event (in other words, just one visit).
        for user_id, deactivating_event_type in enumerate([
                "Tab content loaded (ready)",
                "Tab content loaded (load)",
                "Tab content loaded (pageshow)",
                ]):
            create_location_event(
                user_id=user_id,
                visit_date=time,
                event_type="Tab activated",  # activating event type
                url="http://url1.com",
            )
            time += datetime.timedelta(seconds=1)
            create_location_event(
                user_id=user_id,
                visit_date=time,
                event_type=deactivating_event_type,
                url="http://url1.com",
            )
            time += datetime.timedelta(seconds=1)

        compute_location_visits()
        self.assertEqual(LocationVisit.select().count(), 0)

    def test_handle_switch_between_tabs_with_same_page_as_new_visit(self):

        time = datetime.datetime(2000, 1, 1, 12, 0, 1, 0)

        create_task_period(
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
        )

        # We have seen that sometimes a tab deactivation of the previous tab
        # is reported slightly after the activation of a newly-activated tab.
        # This test case handles this pathological case, by making sure that
        # each tab is considered independently of every other tab.
        create_location_event(
            visit_date=time,
            event_type="Tab activated",
            url="http://url.com",
            tab_id=1,
        )
        create_location_event(
            visit_date=time + datetime.timedelta(seconds=3),
            event_type="Tab activated",
            url="http://url.com",
            tab_id=2,
        )
        create_location_event(
            visit_date=time + datetime.timedelta(seconds=4),
            event_type="Tab deactivated",
            url="http://url.com",
            tab_id=1,
        )
        create_location_event(
            visit_date=time + datetime.timedelta(seconds=3),
            event_type="Tab deactivated",
            url="http://url.com",
            tab_id=2,
        )

        compute_location_visits()
        self.assertEqual(LocationVisit.select().count(), 2)
