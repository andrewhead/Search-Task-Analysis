#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn

from models import QuestionEvent, TaskPeriod


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

CONCERN_COUNT = 6  # needs to be updated to reflect count of concerns in our study


def _get_concern_index(user_id, task_index):
    '''
    Compute the index of a concern assigned to a user for a task.
    This re-applies the counter-balancing logic from our study design here, so that
    we can recover the the questions that participants were answering for each task.
    '''
    offset = user_id % CONCERN_COUNT
    return (offset + task_index) % CONCERN_COUNT


def compute_task_periods():

    # Create a new index for this computation
    last_compute_index = TaskPeriod.select(fn.Max(TaskPeriod.compute_index)).scalar() or 0
    compute_index = last_compute_index + 1

    # Compute the ID of the last user to complete the study
    max_user_id = QuestionEvent.select(fn.Max(QuestionEvent.user_id)).scalar()

    # Compute the time that each user spends in each question
    for user_id in range(0, max_user_id + 1):

        question_events = (
            QuestionEvent
            .select()
            .where(QuestionEvent.user_id == user_id)
            .order_by(QuestionEvent.time.asc())
            )

        start_task_event = None

        for question_event in question_events:

            # If the 'task' page has been loaded, store the question event that started it.
            if question_event.event_type == 'get task':
                start_task_event = question_event

            elif question_event.event_type == 'post task':

                if start_task_event is not None:

                    # Save an event if the index of task for a 'post' event that comes
                    # after a task starts matches the task index of the event that started it.
                    if question_event.question_index == start_task_event.question_index:
                        TaskPeriod.create(
                            compute_index=compute_index,
                            user_id=user_id,
                            task_index=question_event.question_index,
                            concern_index=_get_concern_index(
                                user_id, question_event.question_index),
                            start=start_task_event.time,
                            end=question_event.time,
                        )

                # As long as we have seen an event for the end of a task, reset
                # state such that no "start task" event has been seen
                start_task_event = None


def main(*args, **kwargs):
    compute_task_periods()


def configure_parser(parser):
    parser.description = "Compute the time bounds of all visits to URLs on the web."
