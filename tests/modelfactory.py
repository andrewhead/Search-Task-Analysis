#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import datetime

from models import QuestionEvent


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
