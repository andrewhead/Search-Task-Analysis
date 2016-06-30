#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import datetime

from compute.task_periods import compute_task_periods
from tests.base import TestCase
from tests.modelfactory import create_question_event
from models import QuestionEvent, TaskPeriod


logger = logging.getLogger('data')


class ComputeTaskPeriodTest(TestCase):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(
            [QuestionEvent, TaskPeriod],
            *args, **kwargs
        )

    def test_make_task_period(self):

        # Setup: create two events bounding a single task
        START_TIME = datetime.datetime(2000, 1, 1, 12, 0, 1, 0)
        create_question_event(time=START_TIME, event_type='get task')
        create_question_event(
            time=START_TIME + datetime.timedelta(seconds=1),
            event_type='post responses'
        )

        # Test: make sure a task has been created with the time bounds of the
        # events that started and ended it.
        compute_task_periods()
        task_periods = TaskPeriod.select()
        self.assertEqual(task_periods.count(), 1)
        period = task_periods[0]
        self.assertEqual(period.user_id, 0)
        self.assertEqual(period.start, datetime.datetime(2000, 1, 1, 12, 0, 1, 0))
        self.assertEqual(period.end, datetime.datetime(2000, 1, 1, 12, 0, 2, 0))

    def test_skip_task_period_with_unmatching_task_indexes(self):

        START_TIME = datetime.datetime(2000, 1, 1, 12, 0, 1, 0)
        create_question_event(question_index=0, time=START_TIME, event_type='get task')
        create_question_event(
            question_index=1,
            time=START_TIME + datetime.timedelta(seconds=1),
            event_type='post responses'
        )

        compute_task_periods()
        task_periods = TaskPeriod.select()
        self.assertEqual(task_periods.count(), 0)

    def test_make_task_only_if_both_events_from_one_user(self):

        START_TIME = datetime.datetime(2000, 1, 1, 12, 0, 1, 0)
        create_question_event(user_id=0, time=START_TIME, event_type='get task')
        create_question_event(
            user_id=1,
            time=START_TIME + datetime.timedelta(seconds=1),
            event_type='post responses'
        )

        compute_task_periods()
        task_periods = TaskPeriod.select()
        self.assertEqual(task_periods.count(), 0)

    def test_make_tasks_with_events_interleaved_between_users(self):

        START_TIME = datetime.datetime(2000, 1, 1, 12, 0, 1, 0)
        create_question_event(user_id=0, time=START_TIME, event_type='get task')
        create_question_event(
            user_id=1,
            time=START_TIME + datetime.timedelta(seconds=1),
            event_type='get task'
        )
        create_question_event(
            user_id=0,
            time=START_TIME + datetime.timedelta(seconds=2),
            event_type='post responses'
        )
        create_question_event(
            user_id=1,
            time=START_TIME + datetime.timedelta(seconds=3),
            event_type='post responses'
        )

        compute_task_periods()
        task_periods = TaskPeriod.select()
        self.assertEqual(task_periods.count(), 2)
        user_ids = [task_period.user_id for task_period in TaskPeriod.select()]
        self.assertIn(0, user_ids)
        self.assertIn(1, user_ids)
