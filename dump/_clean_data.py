#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging


logger = logging.getLogger('data')


def normalize_user_id(database_user_id):
    '''
    We use two different numbering schemes for participants.
    One of them is determined by the order in which participants were added to our
    experiment's database.  The other one is the index with which they took part
    in our study, and is used in our MAXQDA notes.
    This method converts the user index in the database to a user ID that we
    used when taking experiment notes, to allow for easy comparison with our notes.
    '''
    if database_user_id == 7:
        return 1
    elif database_user_id == 5:
        return 2
    elif database_user_id == 6:
        return 3
    elif database_user_id > 7:
        return database_user_id - 4
