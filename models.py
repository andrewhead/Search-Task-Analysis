#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import datetime
import json
import copy
from peewee import Model, SqliteDatabase, Proxy, PostgresqlDatabase,\
    IntegerField, DateTimeField, TextField, BooleanField


logger = logging.getLogger('data')

POSTGRES_CONFIG_NAME = 'postgres-credentials.json'
DATABASE_NAME = 'searchlogger'
db_proxy = Proxy()


class BatchInserter(object):
    '''
    A class for saving database records in batches.
    Save rows to the batch inserter, and it will save the rows to
    the database after it has been given a batch size of rows.
    Make sure to call the `flush` method when you're finished using it
    to save any rows that haven't yet been saved.

    Assumes all models have been initialized to connect to db_proxy.
    '''
    def __init__(self, ModelType, batch_size, fill_missing_fields=False):
        '''
        ModelType is the Peewee model to which you want to save the data.
        If the rows you save will have fields missing for some of the records,
        set `fill_missing_fields` to true so that all rows will be augmented
        with all fields to prevent Peewee from crashing.
        '''
        self.rows = []
        self.ModelType = ModelType
        self.batch_size = batch_size
        self.pad_data = fill_missing_fields

    def insert(self, row):
        '''
        Save a row to the database.
        Each row is a dictionary of key-value pairs, where each key is the name of a field
        and each value is the value of the row for that column.
        '''
        self.rows.append(row)
        if len(self.rows) >= self.batch_size:
            self.flush()

    def flush(self):
        if self.pad_data:
            self._pad_data(self.rows)
        with db_proxy.atomic():
            self.ModelType.insert_many(self.rows).execute()
        self.rows = []

    def _pad_data(self, rows):
        '''
        Before we can bulk insert rows using Peewee, they all need to have the same
        fields.  This method adds the missing fields to all rows to make
        sure they all describe the same fields.  It does this destructively
        to the rows provided as input.
        '''
        # Collect the union of all field names
        field_names = set()
        for row in rows:
            field_names = field_names.union(row.keys())

        # We'll enforce that default for all unspecified fields is NULL
        default_data = {field_name: None for field_name in field_names}

        # Pad each row with the missing fields
        for i, _ in enumerate(rows):
            updated_data = copy.copy(default_data)
            updated_data.update(rows[i])
            rows[i] = updated_data


class ProxyModel(Model):
    ''' A peewee model that is connected to the proxy defined in this module. '''

    class Meta:
        database = db_proxy


class LocationEvent(ProxyModel):
    ''' A browser event describing when a user visits a new location. '''

    user_id = IntegerField()
    visit_date = DateTimeField()
    log_date = DateTimeField()
    tab_id = TextField()
    tab_index = IntegerField()
    title = TextField()
    url = TextField()
    event_type = TextField()

    class Meta:
        db_table = 'searchlogger_locationevent'


class QuestionEvent(ProxyModel):
    ''' A user interface of a participant interacting with our form. '''

    user_id = IntegerField()
    question_index = IntegerField()
    time = DateTimeField()
    event_type = TextField()

    class Meta:
        db_table = 'form_questionevent'


class TaskPeriod(ProxyModel):
    ''' A time period that a user spends on a task from our form. '''

    # Keep a record of when this record was computed
    compute_index = IntegerField(index=True)
    date = DateTimeField(default=datetime.datetime.now)

    user_id = IntegerField(index=True)
    task_index = IntegerField(index=True)
    concern_index = IntegerField(index=True)
    start = DateTimeField()
    end = DateTimeField()


class LocationVisit(ProxyModel):
    ''' A time period that a user spends at a location on the web. '''

    # Keep a record of when this record was computed
    compute_index = IntegerField(index=True)
    date = DateTimeField(default=datetime.datetime.now)

    user_id = IntegerField(index=True)
    task_index = IntegerField(index=True)
    concern_index = IntegerField(index=True)
    url = TextField(index=True)
    tab_id = TextField(index=True)
    title = TextField()
    start = DateTimeField()
    end = DateTimeField()


class LocationRating(ProxyModel):
    ''' A user rating of a location they found for a task. '''

    # Keep a record of when this record was computed
    compute_index = IntegerField(index=True)
    date = DateTimeField(default=datetime.datetime.now)

    user_id = IntegerField(index=True)
    task_index = IntegerField(index=True)
    concern_index = IntegerField(index=True)
    url = TextField(index=True)
    title = TextField()
    rating = IntegerField(index=True)
    visit_date = DateTimeField()


class Question(ProxyModel):
    '''
    Answers to a set of follow-up questions we ask users after
    each of our study's search tasks.
    '''

    user_id = IntegerField()
    question_index = IntegerField()
    concern = TextField()
    likert_comparison_evidence = IntegerField()
    na_likert_comparison_evidence = BooleanField()
    evidence = TextField()
    likert_confidence = IntegerField()
    na_likert_confidence = BooleanField()

    class Meta:
        db_table = 'form_question'


class PackagePair(ProxyModel):
    ''' A pair of packages that participants have chosen to learn about for the study. '''

    user_id = IntegerField()
    package1 = TextField()
    package2 = TextField()

    class Meta:
        db_table = 'form_packagepair'


class PackageComparison(ProxyModel):
    '''
    A comparison between packages that participants give at the beginning and end of the study.
    '''

    user_id = IntegerField()
    stage = TextField()
    likert_preference = IntegerField()
    likert_quality = IntegerField()

    class Meta:
        db_table = 'form_packagecomparison'


class Postquestionnaire(ProxyModel):
    ''' Questions we ask participants once they are finished with the study. '''

    user_id = IntegerField()
    concern_rank1 = TextField()
    concern_rank2 = TextField()
    concern_rank3 = TextField()
    concern_rank4 = TextField()
    concern_rank5 = TextField()
    concern_rank6 = TextField()
    likert_perception_change = IntegerField()

    class Meta:
        db_table = 'form_postquestionnaire'


class Strategy(ProxyModel):
    ''' Participants' self-reported strategies for search before a task. '''

    user_id = IntegerField()
    strategy = TextField()
    question_index = IntegerField()

    class Meta:
        db_table = 'form_strategy'


def init_database(db_type, config_filename=None):

    if db_type == 'postgres':

        # If the user wants to use Postgres, they should define their credentials
        # in an external config file, which are used here to access the database.
        config_filename = config_filename if config_filename else POSTGRES_CONFIG_NAME
        with open(config_filename) as pg_config_file:
            pg_config = json.load(pg_config_file)

        config = {}
        config['user'] = pg_config['dbusername']
        if 'dbpassword' in pg_config:
            config['password'] = pg_config['dbpassword']
        if 'host' in pg_config:
            config['host'] = pg_config['host']
        if 'port' in pg_config:
            config['port'] = pg_config['port']

        db = PostgresqlDatabase(DATABASE_NAME, **config)

    # Sqlite is the default type of database.
    elif db_type == 'sqlite' or not db_type:
        db = SqliteDatabase(DATABASE_NAME + '.db')

    db_proxy.initialize(db)


def create_tables():
    db_proxy.create_tables([
        TaskPeriod,
        LocationVisit,
        LocationRating,
    ], safe=True)
