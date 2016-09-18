#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn
import re

from models import TaskPeriod, LocationEvent, LocationRating


logger = logging.getLogger('data')


def create_location_rating(compute_index, task_compute_index, event, rating):
    ''' Returns True if this rating could be matched to an existing task, False otherwise. '''

    # Search for a task that this rating could have occurred within.
    # If we successfully find a task, then save the rating event.
    task_periods = (
        TaskPeriod.select()
        .where(
            TaskPeriod.compute_index == task_compute_index,
            TaskPeriod.user_id == event.user_id,
            TaskPeriod.start < event.visit_date,
            TaskPeriod.end > event.visit_date,
        )
    )
    if task_periods.count() > 0:
        task_period = task_periods[0]
        LocationRating.create(
            compute_index=compute_index,
            user_id=event.user_id,
            task_index=task_period.task_index,
            concern_index=task_period.concern_index,
            url=event.url,
            rating=rating,
            title=event.title,
            visit_date=event.visit_date,
        )

    return (task_periods.count() > 0)


def compute_location_ratings(task_compute_index=None):

    # Create a new index for this computation
    last_compute_index = LocationRating.select(fn.Max(LocationRating.compute_index)).scalar() or 0
    compute_index = last_compute_index + 1

    # Determine what will be the compute index of the task periods that ratings are matched to.
    # This will become the latest compute index if it hasn't been specified.
    if task_compute_index is None:
        task_compute_index = TaskPeriod.select(fn.Max(TaskPeriod.compute_index)).scalar()

    # Create a list to hold all ratings that couldn't be matched to a task period.
    # At the end, we want to return these, in case it's important for the caller to know
    # which events we couldn't create rating records for.
    unmatched_ratings = []

    for event in LocationEvent.select():

        # Check to see whether this is a rating event
        rating_match = re.match("^Rating: (\d)+$", event.event_type)
        if rating_match:

            # If this is a rating event, extract the rating
            rating = int(rating_match.group(1))
            rating_created = create_location_rating(
                compute_index=compute_index,
                task_compute_index=task_compute_index,
                event=event,
                rating=rating
            )

            # If a rating wasn't created, this probably couldn't be matched to a task.
            # Save a record of which event failed to be matched to a task and which user
            # this event happened for.
            if not rating_created:
                unmatched_ratings.append({
                    'user_id': event.user_id,
                    'event_id': event.id,
                })

    return unmatched_ratings


def main(task_compute_index, *args, **kwargs):

    unmatched_rating_events = compute_location_ratings(task_compute_index)

    # Report all events that could not be matched to a task and, thus, for which
    # we did not create a location rating.
    for event in unmatched_rating_events:
        logger.warn(
            "Could not find matching task for event %d (user %d)",
            event['event_id'],
            event['user_id'],
        )


def configure_parser(parser):
    parser.description = "Compute a table of all ratings for locations participants visited."
    parser.add_argument(
        '--task-compute-index',
        type=int,
        help="Which version of task periods to match visits to (default: latest)."
    )
