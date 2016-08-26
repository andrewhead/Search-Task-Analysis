#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn
import datetime

from models import QuestionEvent, TaskPeriod


logger = logging.getLogger('data')
CONCERN_COUNT = 6  # needs to be updated to reflect count of concerns in our study

# A tuple of task periods that we want to discard.
# We discard all task periods for each user-task index pair.
# We found that there are a number of false detections.
# This is our way of removing them.
# At this time, all task periods with that user and task index are discarded, even
# if only one is incorrect.  If any of the detected task periods are wrongly discarded,
# you should at them back in with the `EXTRA_TASK_PERIODS` tuple.
# For additional notes on why these tasks were incorrectly detected and how we corrected them,
# email <andrewhead@berkeley.edu> for research notes.
DISCARD_TASK_PERIODS = (
    {'user_id': 5, 'task_index': 4},
    {'user_id': 6, 'task_index': 0},
    {'user_id': 9, 'task_index': 0},
    {'user_id': 11, 'task_index': 2},
    {'user_id': 13, 'task_index': 6},
    {'user_id': 15, 'task_index': 0},
    {'user_id': 16, 'task_index': 0},
    {'user_id': 16, 'task_index': 1},
    {'user_id': 16, 'task_index': 3},
    {'user_id': 17, 'task_index': 1},
    {'user_id': 17, 'task_index': 2},
    {'user_id': 20, 'task_index': 0},
)

# These task periods will be added in after all task periods have been detected
# and those matching the discard patterns have been discarded.
# A task period is defined by a user ID, a task index, and a start and end time
EXTRA_TASK_PERIODS = ({
    'user_id': 5,
    'task_index': 4,
    'start': datetime.datetime(2016, 6, 20, 14, 31, 58),
    'end': datetime.datetime(2016, 6, 20, 14, 36, 35),
}, {
    'user_id': 6,
    'task_index': 0,
    'start': datetime.datetime(2016, 6, 20, 15, 46, 16),
    'end': datetime.datetime(2016, 6, 20, 15, 52, 49),
}, {
    'user_id': 9,
    'task_index': 0,
    'start': datetime.datetime(2016, 6, 22, 18, 18, 22),
    'end': datetime.datetime(2016, 6, 22, 18, 24, 40),
}, {
    'user_id': 11,
    'task_index': 2,
    'start': datetime.datetime(2016, 6, 24, 9, 47, 24),
    'end': datetime.datetime(2016, 6, 24, 9, 52, 20),
}, {
    'user_id': 13,
    'task_index': 6,
    'start': datetime.datetime(2016, 6, 29, 11, 10, 49),
    'end': datetime.datetime(2016, 6, 29, 11, 11, 59),
}, {
    'user_id': 15,
    'task_index': 0,
    'start': datetime.datetime(2016, 7, 1, 16, 30, 40),
    'end': datetime.datetime(2016, 7, 1, 16, 39, 13),
}, {
    'user_id': 16,
    'task_index': 0,
    'start': datetime.datetime(2016, 7, 6, 18, 21, 13),
    'end': datetime.datetime(2016, 7, 6, 18, 28, 4),
}, {
    'user_id': 16,
    'task_index': 1,
    'start': datetime.datetime(2016, 7, 6, 18, 33, 1),
    'end': datetime.datetime(2016, 7, 6, 18, 43, 30),
}, {
    'user_id': 16,
    'task_index': 3,
    'start': datetime.datetime(2016, 7, 6, 19, 3, 35),
    'end': datetime.datetime(2016, 7, 6, 19, 9, 53),
}, {
    'user_id': 20,
    'task_index': 0,
    'start': datetime.datetime(2016, 7, 13, 16, 19, 44),
    'end': datetime.datetime(2016, 7, 13, 16, 26, 28),
})


def _get_concern_index(user_id, task_index):
    '''
    Compute the index of a concern assigned to a user for a task.
    This re-applies the counter-balancing logic from our study design here, so that
    we can recover the the questions that participants were answering for each task.

    Typically, this routine will return a "concern index" between 0 and (CONCERN_COUNT - 1)
    To disambiguate the 0th task (the introductory task) from the rest, this method returns -1 .
    '''
    if task_index == 0:
        return -1
    offset = user_id % CONCERN_COUNT
    return (offset + task_index) % CONCERN_COUNT


def compute_task_periods(discard_periods=DISCARD_TASK_PERIODS, extra_periods=EXTRA_TASK_PERIODS):

    # Create a new index for this computation
    last_compute_index = TaskPeriod.select(fn.Max(TaskPeriod.compute_index)).scalar() or 0
    compute_index = last_compute_index + 1

    # Compute the ID of the last user to complete the study
    max_user_id = QuestionEvent.select(fn.Max(QuestionEvent.user_id)).scalar() or 0

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

                        # Only save a task period if its user and index are not in the discard list.
                        task_discard_specification = {
                            'user_id': user_id,
                            'task_index': question_event.question_index,
                        }
                        if task_discard_specification not in discard_periods:
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

    # The caller may have provided a list of extra task periods to append to the computed results.
    # Add these records in one by one.
    for period_data in extra_periods:
        TaskPeriod.create(
            compute_index=compute_index,
            user_id=period_data['user_id'],
            task_index=period_data['task_index'],
            concern_index=_get_concern_index(period_data['user_id'], period_data['task_index']),
            start=period_data['start'],
            end=period_data['end'],
        )


def main(*args, **kwargs):
    compute_task_periods()


def configure_parser(parser):
    parser.description = "Compute the time bounds of all tasks a user completed in our form."
