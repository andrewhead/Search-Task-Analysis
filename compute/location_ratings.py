#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn
import re

from models import TaskPeriod, LocationEvent, LocationRating


logger = logging.getLogger('data')


def create_location_rating(compute_index, task_compute_index, event, rating):

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


def compute_location_ratings(task_compute_index=None):

    # Create a new index for this computation
    last_compute_index = LocationRating.select(fn.Max(LocationRating.compute_index)).scalar() or 0
    compute_index = last_compute_index + 1

    # Determine what will be the compute index of the task periods that ratings are matched to.
    # This will become the latest compute index if it hasn't been specified.
    if task_compute_index is None:
        task_compute_index = TaskPeriod.select(fn.Max(TaskPeriod.compute_index)).scalar()

    for event in LocationEvent.select():

        # Check to see whether this is a rating event
        rating_match = re.match("^Rating: (\d)+$", event.event_type)
        if rating_match:

            # If this is a rating event, extract the rating
            rating = int(rating_match.group(1))
            create_location_rating(
                compute_index=compute_index,
                task_compute_index=task_compute_index,
                event=event,
                rating=rating
            )


def main(task_compute_index, *args, **kwargs):
    compute_location_ratings(task_compute_index)


def configure_parser(parser):
    parser.description = "Compute a table of all ratings for locations participants visited."
    parser.add_argument(
        '--task-compute-index',
        type=int,
        help="Which version of task periods to match visits to (default: latest)."
    )
