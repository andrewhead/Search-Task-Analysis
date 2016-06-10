#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn

from models import TaskPeriod, LocationEvent, LocationVisit


logger = logging.getLogger('data')


# These events suggest that a URL has been 'activated' and is being watched
ACTIVATING_EVENTS = [
    'Tab opened',
    'Tab activated',
    'Tab content loaded',
    'Window activated'
]

# These events suggest that the *previous* URL is now no longer being watched
DEACTIVATING_EVENTS = [
    'Tab opened',
    'Tab activated',
    'Tab content loaded',
    'Window activated',
    'Window deactivated'
]


def compute_location_visits():

    # Create a new index for this computation
    last_compute_index = LocationVisit.select(fn.Max(LocationVisit.compute_index)).scalar() or 0
    compute_index = last_compute_index + 1

    # Compute the ID of the last user to complete the study
    max_user_id = LocationEvent.select(fn.Max(LocationEvent.user_id)).scalar()

    # Compute the time that each user spends in each question
    for user_id in range(0, max_user_id + 1):

        # Fetch the events for all locations the user has visited
        location_events = (
            LocationEvent
            .select()
            .where(LocationEvent.user_id == user_id)
            .order_by(LocationEvent.visit_date.asc())
            )

        activating_event = None

        for location_event in location_events:

            # For deactivating events that follow an activating event, we have
            # reached the end of a visit to a URL.  Find out if there's an associated task and,
            # if there is, store a record of this visit
            if location_event.event_type in DEACTIVATING_EVENTS:
                if activating_event is not None:
                    task_periods = (
                        TaskPeriod.select()
                        .where(
                            TaskPeriod.user_id == user_id,
                            TaskPeriod.start < activating_event.visit_date,
                            TaskPeriod.end > location_event.visit_date,
                        )
                    )
                    # If we successfully fetched a task whose period matched the
                    # bounds of this location event, create a record of the visit
                    if task_periods.count() > 0:
                        task_period = task_periods[0]
                        LocationVisit.create(
                            compute_index=compute_index,
                            user_id=user_id,
                            task_index=task_period.task_index,
                            concern_index=task_period.concern_index,
                            start=activating_event.visit_date,
                            end=location_event.visit_date,
                            url=activating_event.url,
                            title=activating_event.title,
                        )

                # Set the activating event back to a null value so that we don't
                # keep waiting for the end of an event.
                activating_event = None

            # If this event has a type that means a user started looking at a page,
            # then save a reference to this event so we can construct
            if location_event.event_type in ACTIVATING_EVENTS:
                activating_event = location_event


def main(*args, **kwargs):
    compute_location_visits()


def configure_parser(parser):
    parser.description = "Compute the time bounds of all visits to URLs on the web."
