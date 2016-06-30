#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn

from models import TaskPeriod, LocationEvent, LocationVisit


logger = logging.getLogger('data')


# We start at task 1 instead of 0 for now, as our analysis hasn't yet
# included any of the preliminary search tasks.
TASK_COUNT = 6
FIRST_TASK = 1
TASK_RANGE = range(FIRST_TASK, FIRST_TASK + TASK_COUNT)

# These events suggest that a tab has been 'activated' and is now being visited
ACTIVATING_EVENTS = [
    "Tab activated",
    "Window activated",
]

# These event suggest that no tabs are being visited anymore.
DEACTIVATING_EVENTS = [
    "Window deactivated",
]

# These events suggest that a new URL has been loaded into a tab
NEW_PAGE_EVENTS = [
    "Tab content loaded (load)",
    "Tab content loaded (ready)",
    "Tab content loaded (pageshow)",
]


def create_location_visit(
        compute_index, task_period, user_id,
        activating_event, deactivating_event):
    '''
    Create a record of the start and end of a visit to a URL within a tab.
    Note that while an `activating_event` will necessarily be associated with the URL
    and page title for the visited page, the deactivating event may be associated
    with a different URL and page.
    '''
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


def compute_location_visits(task_compute_index=None):

    # Create a new index for this computation
    last_compute_index = LocationVisit.select(fn.Max(LocationVisit.compute_index)).scalar() or 0
    compute_index = last_compute_index + 1

    # Determine what will be the compute index of the task periods that these visits are matched to.
    # This will become the latest compute index if it hasn't been specified.
    if task_compute_index is None:
        task_compute_index = TaskPeriod.select(fn.Max(TaskPeriod.compute_index)).scalar()

    # Compute the ID of the last user to complete the study
    max_user_id = LocationEvent.select(fn.Max(LocationEvent.user_id)).scalar()

    # Compute the time that each user spends in each question
    for user_id in range(0, max_user_id + 1):

        # Visit all tasks for each user
        for task_index in TASK_RANGE:

            # Fetch the period of time for this task
            task_periods = (
                TaskPeriod.select()
                .where(
                    TaskPeriod.compute_index == task_compute_index,
                    TaskPeriod.task_index == task_index,
                    TaskPeriod.user_id == user_id,
                )
            )
            if task_periods.count() < 1:
                continue
            task_period = task_periods[0]

            # Fetch the events for all locations the user has visited during this task
            location_events = (
                LocationEvent
                .select()
                .where(
                    LocationEvent.user_id == user_id,
                    LocationEvent.log_date >= task_period.start,
                    LocationEvent.log_date <= task_period.end,
                )
                .order_by(LocationEvent.visit_date.asc())
            )

            # In the space below, we assemble "visits" from sequences of events.
            # This dictionary maps a tab-URL tuple to the event that made it active.
            active_tab_id = None
            active_tab_latest_url_event = None

            for event in location_events:

                # When a new page is loaded in the current tab, this is the end of the
                # last event and the start of a new one (that will be in the same tab).
                if event.event_type in NEW_PAGE_EVENTS:
                    if active_tab_id is not None and event.tab_id == active_tab_id:
                        if event.url != active_tab_latest_url_event.url:
                            create_location_visit(
                                compute_index=compute_index,
                                task_period=task_period,
                                user_id=user_id,
                                activating_event=active_tab_latest_url_event,
                                deactivating_event=event,
                            )
                            active_tab_latest_url_event = event

                # If the window has been deactivated, then end the visit in the current tab
                if event.event_type in DEACTIVATING_EVENTS:
                    if active_tab_id is not None:
                        create_location_visit(
                            compute_index=compute_index,
                            task_period=task_period,
                            user_id=user_id,
                            activating_event=active_tab_latest_url_event,
                            deactivating_event=event,
                        )
                        active_tab_id = None
                        active_tab_latest_url_event = None

                # If a tab or window has been activated, that tab is now active.
                if event.event_type in ACTIVATING_EVENTS:

                    # End any visits in progress for other tabs
                    if active_tab_id is not None:
                        create_location_visit(
                            compute_index=compute_index,
                            task_period=task_period,
                            user_id=user_id,
                            activating_event=active_tab_latest_url_event,
                            deactivating_event=event,
                        )

                    # Set the new active tab
                    active_tab_id = event.tab_id
                    active_tab_latest_url_event = event


def main(task_compute_index, *args, **kwargs):
    compute_location_visits(task_compute_index)


def configure_parser(parser):
    parser.description = "Compute the time bounds of all visits to URLs on the web."
    parser.add_argument(
        '--task-compute-index',
        type=int,
        help="Which version of task periods to match visits to (default: latest)."
    )
