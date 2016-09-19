#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn
import re

from models import TaskPeriod, LocationEvent, LocationRating


logger = logging.getLogger('data')

# Some of these ratings could not be matched to tasks, because they fell outside of
# the formal task period that we defined.  So, here are a set of hand labels that
# will be used by default for matching events to tasks.
HAND_LABELED_EVENTS = [
    {'user_id': 7, 'event_id': 4440, 'task_index': 6},
    {'user_id': 7, 'event_id': 4443, 'task_index': 6},
    {'user_id': 5, 'event_id': 4736, 'task_index': 1},
    {'user_id': 5, 'event_id': 4863, 'task_index': 2},
    {'user_id': 5, 'event_id': 4866, 'task_index': 2},
    {'user_id': 5, 'event_id': 4999, 'task_index': 3},
    {'user_id': 5, 'event_id': 5020, 'task_index': 3},
    {'user_id': 5, 'event_id': 5026, 'task_index': 3},
    {'user_id': 5, 'event_id': 5038, 'task_index': 3},
    {'user_id': 5, 'event_id': 5042, 'task_index': 3},
    {'user_id': 5, 'event_id': 5046, 'task_index': 3},
    {'user_id': 6, 'event_id': 6174, 'task_index': 6},
    {'user_id': 6, 'event_id': 6196, 'task_index': 6},
    {'user_id': 10, 'event_id': 7962, 'task_index': 2},
    {'user_id': 10, 'event_id': 7973, 'task_index': 2},
    {'user_id': 10, 'event_id': 8225, 'task_index': 5},
    {'user_id': 10, 'event_id': 8228, 'task_index': 5},
    {'user_id': 17, 'event_id': 14311, 'task_index': 3},
    {'user_id': 19, 'event_id': 16080, 'task_index': 3},
    {'user_id': 19, 'event_id': 16083, 'task_index': 3},
    {'user_id': 20, 'event_id': 17056, 'task_index': 6},
    {'user_id': 20, 'event_id': 17059, 'task_index': 6},
]


def create_location_rating(compute_index, task_compute_index, event, rating, labels):
    ''' Returns True if this rating could be matched to an existing task, False otherwise. '''

    # Check for hand-written task index labels for this event
    matching_labels = filter(lambda l: l['event_id'] == event.id, labels)
    if len(matching_labels) > 0:
        task_index = matching_labels[0]['task_index']
        task_periods = (
            TaskPeriod.select()
            .where(
                TaskPeriod.compute_index == task_compute_index,
                TaskPeriod.task_index == task_index,
                TaskPeriod.user_id == event.user_id,
            )
        )
        hand_aligned = True
    # If a hand-written label wasn't found, search for a task that this rating could have
    # occurred within.  If we successfully find a task, then save the rating event.
    else:
        task_periods = (
            TaskPeriod.select()
            .where(
                TaskPeriod.compute_index == task_compute_index,
                TaskPeriod.user_id == event.user_id,
                TaskPeriod.start < event.log_date,
                TaskPeriod.end > event.log_date,
            )
        )
        hand_aligned = False
    # If a matching task has been found, then save the rating alongside that task.
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
            hand_aligned=hand_aligned,
        )

    return (task_periods.count() > 0)


def compute_location_ratings(labels=HAND_LABELED_EVENTS, task_compute_index=None):

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
                rating=rating,
                labels=labels,
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

    unmatched_rating_events = compute_location_ratings(task_compute_index=task_compute_index)

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
