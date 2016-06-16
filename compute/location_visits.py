#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn

from models import TaskPeriod, LocationEvent, LocationVisit


logger = logging.getLogger('data')


# These events suggest that a URL has been 'activated' and is now being visited
ACTIVATING_EVENTS = [
    "Tab opened",
    "Tab content loaded (pageshow)",
    "Tab activated",
    "Window activated",
]

# For the current URL, these events suggest it is no longer being visited
DEACTIVATING_EVENTS = [
    "Tab closed",
    "Tab deactivated",
    "Window deactivated",
]

# For a *new* URL, these events suggest that all past URLs are no longer being visited
NEW_PAGE_EVENTS = [
    "Tab content loaded (load)",
    "Tab content loaded (ready)",
    "Tab content loaded (pageshow)",
]


def create_location_visit(compute_index, user_id, activating_event, deactivating_event):
    '''
    Create a record of the start and end of a visit to a URL within a tab.
    Note that while an `activating_event` will necessarily be associated with the URL
    and page title for the visited page, the deactivating event may be associated
    with a different URL and page.
    '''

    # When a visit to a URL is complete, find out if there's an associated task and,
    # if there is, store a record of this visit
    task_periods = (
        TaskPeriod.select()
        .where(
            TaskPeriod.user_id == user_id,
            TaskPeriod.start < activating_event.visit_date,
            TaskPeriod.end > deactivating_event.visit_date,
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
            end=deactivating_event.visit_date,
            url=activating_event.url,
            title=activating_event.title,
            tab_id=activating_event.tab_id,
        )


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

        # This dictionary maps a tab-URL tuple to the event that made it active.
        active_visits = {}
        key = lambda event: (event.tab_id, event.url)

        for event in location_events:

            # When a new page is loaded, any pages that don't have the new page's
            # URL and tab are now no longer being visited.
            if event.event_type in NEW_PAGE_EVENTS:
                for (tab_id, url), activating_event in active_visits.items():
                    if not (tab_id == event.tab_id and url == event.url):
                        create_location_visit(
                            compute_index=compute_index,
                            user_id=user_id,
                            activating_event=activating_event,
                            deactivating_event=event,
                        )
                        del active_visits[(tab_id, url)]

            # If a tab or window has been deactivated, then end the visit to
            # the location for the URL deactivated.
            if event.event_type in DEACTIVATING_EVENTS:
                if key(event) in active_visits:
                    activating_event = active_visits[key(event)]
                    create_location_visit(
                        compute_index=compute_index,
                        user_id=user_id,
                        activating_event=activating_event,
                        deactivating_event=event,
                    )
                    del active_visits[key(event)]

            # If a URL has been activated for a tab (and isn't yet in the list of activated
            # URLs), then save it in the list of activated pages
            if event.event_type in ACTIVATING_EVENTS:
                if key(event) not in active_visits:
                    active_visits[key(event)] = event


def main(*args, **kwargs):
    compute_location_visits()


def configure_parser(parser):
    parser.description = "Compute the time bounds of all visits to URLs on the web."
