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
            tab_id='1',
            url="http://url1.com"
        )
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
            event_type="Tab activated",
            tab_id='2',
            url="http://url2.com"
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
            tab_id='1',
            url="http://url1.com"
        )
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 6, 0),
            event_type="Tab activated",
            tab_id='2',
            url="http://url2.com"
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
            tab_id='1',
            url="http://url1.com"
        )
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 1, 0, 0),
            event_type="Tab activated",
            tab_id='2',
            url="http://url1.com"
        )
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 3, 0, 0),
            event_type="Tab activated",
            tab_id='1',
            url="http://url2.com"
        )
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 3, 0, 0),
            event_type="Tab activated",
            tab_id='2',
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
            tab_id='1',
            url="http://url1.com"
        )
        create_location_event(
            user_id=0,
            visit_date=datetime.datetime(2000, 1, 1, 11, 0, 2, 0),
            event_type="Tab activated",
            tab_id='2',
            url="http://url1.com"
        )
        create_task_period(
            user_id=1,
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
        )

        self.assertEqual(LocationVisit.select().count(), 0)

    def test_chain_multiple_location_visits_by_activations(self):

        create_task_period(
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
        )
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            event_type="Tab activated",
            url="http://url1.com",
            tab_id='1',
        )
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
            event_type="Tab activated",
            url="http://url2.com",
            tab_id='2',
        )
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 3, 0),
            event_type="Tab activated",
            url="http://url3.com",
            tab_id='3',
        )

        compute_location_visits()
        visits = LocationVisit.select()
        self.assertEqual(visits.count(), 2)
        urls = [visit.url for visit in LocationVisit.select()]
        self.assertIn("http://url1.com", urls)
        self.assertIn("http://url2.com", urls)

    def test_chain_multiple_location_visits_by_page_loads(self):

        create_task_period(
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
        )
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            event_type="Tab activated",
            url="http://url1.com",
            tab_id='1',
        )
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
            event_type="Tab content loaded (pageshow)",
            url="http://url2.com",
            tab_id='1',
        )
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 3, 0),
            event_type="Tab content loaded (ready)",
            url="http://url3.com",
            tab_id='1',
        )
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 4, 0),
            event_type="Tab content loaded (load)",
            url="http://url4.com",
            tab_id='1',
        )

        compute_location_visits()
        visits = LocationVisit.select()
        self.assertEqual(visits.count(), 3)
        urls = [visit.url for visit in LocationVisit.select()]
        self.assertIn("http://url1.com", urls)
        self.assertIn("http://url2.com", urls)
        self.assertIn("http://url3.com", urls)

    def test_ignore_consecutive_page_loads_of_same_url(self):

        create_task_period(
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
        )
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            event_type="Tab activated",
            url="http://url1.com",
            tab_id='1',
        )
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
            event_type="Tab content loaded (pageshow)",
            url="http://url2.com",
            tab_id='1',
        )
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 3, 0),
            event_type="Tab content loaded (ready)",
            url="http://url2.com",
            tab_id='1',
        )

        compute_location_visits()
        visits = LocationVisit.select()
        self.assertEqual(visits.count(), 1)
        urls = [visit.url for visit in LocationVisit.select()]
        self.assertIn("http://url1.com", urls)

    def test_ignore_content_loaded_in_other_tabs(self):

        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            event_type="Tab activated",
            url="http://url1.com",
            tab_id='1',
        )
        create_location_event(
            visit_date=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
            event_type="Tab content loaded (pageshow)",
            url="http://url2.com",
            tab_id='2',
        )

        compute_location_visits()
        visits = LocationVisit.select()
        self.assertEqual(visits.count(), 0)

    def test_acceptable_activating_location_events(self):

        time = datetime.datetime(2000, 1, 1, 12, 0, 1, 0)
        create_task_period(
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
        )

        for activating_event_type in [
                "Tab activated",
                "Window activated",
                ]:
            create_location_event(
                visit_date=time,
                event_type=activating_event_type,
                tab_id='1',
            )
            time += datetime.timedelta(seconds=1)
            create_location_event(
                visit_date=time,
                event_type="Window deactivated",
                tab_id='1',
            )
            time += datetime.timedelta(seconds=1)

        compute_location_visits()
        self.assertEqual(LocationVisit.select().count(), 2)

    def test_window_deactivated_flushes_old_location(self):

        time = datetime.datetime(2000, 1, 1, 12, 0, 1, 0)

        create_task_period(
            start=datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
            end=datetime.datetime(2000, 1, 1, 12, 2, 0, 0),
        )
        create_location_event(
            visit_date=time,
            event_type="Tab activated",
        )
        create_location_event(
            visit_date=time + datetime.timedelta(seconds=1),
            event_type="Window deactivated",
        )
        create_location_event(
            visit_date=time + datetime.timedelta(seconds=2),
            event_type="Tab activated",
        )

        compute_location_visits()

        # Make sure that only one event was created---when the tab was deactivated
        self.assertEqual(LocationVisit.select().count(), 1)

        # Make sure that the event that was created eneded when the window was
        # deactivated, and not when the next tab was activated.
        visits = LocationVisit.select()
        visit = visits[0]
        self.assertEqual(visit.end, datetime.datetime(2000, 1, 1, 12, 0, 2, 0))
