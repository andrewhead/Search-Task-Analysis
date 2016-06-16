#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn
import re

from models import TaskPeriod, LocationEvent, LocationRating


logger = logging.getLogger('data')


def compute_location_ratings():

    # Create a new index for this computation
    last_compute_index = LocationRating.select(fn.Max(LocationRating.compute_index)).scalar() or 0
    compute_index = last_compute_index + 1

    for event in LocationEvent.select():

        # Check to see whether this is a rating event
        rating_match = re.match("^Rating: (\d)+$", event.event_type)
        if rating_match:

            # If this is a rating event, extract the rating
            rating = int(rating_match.group(1))

            # Search for a task that this rating could have occurred within.
            # If we successfully find a task, then save the rating event.
            task_periods = (
                TaskPeriod.select()
                .where(
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


def main(*args, **kwargs):
    compute_location_ratings()


def configure_parser(parser):
    parser.description = "Compute a table of all ratings for locations participants visited."
