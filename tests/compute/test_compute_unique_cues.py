#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging

from compute.unique_cues import compute_unique_cues
from tests.base import TestCase
from models import UniqueCue


logger = logging.getLogger('data')
PAGE_TYPE_LOOKUP = {
    "page1": {"main_type": "page_type_1", "redirect": False},
    "page2": {"main_type": "page_type_2", "redirect": False},
    "redirect": {"main_type": "redirect", "redirect": True},
}


class ComputeLocationVisitsTest(TestCase):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(
            [UniqueCue],
            *args, **kwargs
        )

    def test_url_shared_between_two_users_isnt_unique_for_either(self):

        # Run a routine to compute whether each cue is unique to each participant
        compute_unique_cues([
            {'participant_id': 1, 'cue': "Cue 1"},
            {'participant_id': 2, 'cue': "Cue 1"},
        ])
        unique_cues = UniqueCue.select()

        # Two unique cues should have been created: one for each participant for each cue
        self.assertEqual(unique_cues.count(), 2)
        records = [(c.participant_id, c.cue, c.unique) for c in unique_cues]
        self.assertIn((1, "Cue 1", False), records)
        self.assertIn((2, "Cue 1", False), records)

    def test_only_one_record_appears_per_participant_and_url(self):

        compute_unique_cues([
            {'participant_id': 1, 'cue': "Cue 1"},
            {'participant_id': 1, 'cue': "Cue 1"},
        ])
        unique_cues = UniqueCue.select()
        self.assertEqual(unique_cues.count(), 1)
        records = [(c.participant_id, c.cue, c.unique) for c in unique_cues]
        self.assertIn((1, "Cue 1", True), records)

    def test_url_that_no_one_else_has_visited_is_unique(self):

        compute_unique_cues([
            {'participant_id': 1, 'cue': "Cue 1"},
            {'participant_id': 1, 'cue': "Cue 2"},
            {'participant_id': 2, 'cue': "Cue 1"},
        ])
        unique_cues = UniqueCue.select()
        self.assertEqual(unique_cues.count(), 3)
        records = [(c.participant_id, c.cue, c.unique) for c in unique_cues]
        self.assertIn((1, "Cue 1", False), records)
        self.assertIn((1, "Cue 2", True), records)
        self.assertIn((2, "Cue 1", False), records)
