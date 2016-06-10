#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import datetime

from models import QuestionEvent, LocationEvent, TaskPeriod


logger = logging.getLogger('data')


'''
This file contains functions that help us create models with mostly default properties, but
with the ability to configure any one specific field without having to define the others.
This is particularly helpful when we need to create test data, but don't want our test
logic to include many lines of model definitions.
'''


def create_question_event(**kwargs):
    arguments = {
        'user_id': 0,
        'question_index': 1,
        'time': datetime.datetime.utcnow(),
        'event_type': 'get task',
    }
    arguments.update(kwargs)
    return QuestionEvent.create(**arguments)


def create_location_event(**kwargs):
    arguments = {
        'user_id': 0,
        'visit_date': datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
        'log_date': datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
        'tab_index': 1,
        'title': "Title",
        'url': "http://url.com",
        'event_type': "Tab activated",
    }
    arguments.update(kwargs)
    return LocationEvent.create(**arguments)


def create_task_period(**kwargs):
    arguments = {
        'compute_index': 0,
        'date': datetime.datetime.utcnow(),
        'user_id': 0,
        'task_index': 1,
        'concern_index': 2,
        'start': datetime.datetime(2000, 1, 1, 12, 0, 0, 0),
        'end': datetime.datetime(2000, 1, 1, 12, 0, 3, 0),
    }
    arguments.update(kwargs)
    return TaskPeriod.create(**arguments)
