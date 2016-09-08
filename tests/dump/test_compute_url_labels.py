#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import unittest

from dump._urls import standardize_url


logger = logging.getLogger('data')


class StandardizeUrlTest(unittest.TestCase):

    def test_by_default_standard_url_is_domain_and_path(self):
        standardized = standardize_url("http://site.com/path#fragment?q=query")
        self.assertEqual(standardized, "site.com/path")

    def test_standardization_removes_www_prefix_and_schema(self):
        standardized = standardize_url("http://www.site.com")
        self.assertEqual(standardized, "site.com")

    def test_panda3d_topics_keep_topic_id(self):
        standardized = standardize_url("http://panda3d.org/viewtopic.php?f=1&t=2")
        self.assertEqual(standardized, "panda3d.org/viewtopic.php?t=2")

    def test_panda3d_forums_keep_forum_id(self):
        standardized = standardize_url("http://panda3d.org/viewforum.php?f=1")
        self.assertEqual(standardized, "panda3d.org/viewforum.php?f=1")

    def test_panda3d_screenshots_show_keep_shot_name(self):
        # We found that some of our experimental data includes slashes in the name
        # of the shot, so we replicate that here.
        standardized = standardize_url(
            "http://panda3d.org/showss.php?shot=path/to/photo&otherparam=1"
        )
        self.assertEqual(standardized, "panda3d.org/showss.php?shot=path/to/photo")

    def test_youtube_videos_preserve_v_parameter(self):
        standardized = standardize_url("http://youtube.com/watch?v=DRR9fOXkfRE")
        self.assertEqual(standardized, "youtube.com/watch?v=DRR9fOXkfRE")

    def test_google_groups_topic_keep_fragment(self):
        standardized = standardize_url(
            "http://groups.google.com/forum/#!topic/keras-users/epFdzcxl8Gg"
        )
        self.assertEqual(standardized, "groups.google.com/forum/!topic/keras-users/epFdzcxl8Gg")

    def test_google_groups_forums_keep_fragment(self):
        standardized = standardize_url("http://groups.google.com/forum/#!forum/keras-users")
        self.assertEqual(standardized, "groups.google.com/forum/!forum/keras-users")

    def test_google_groups_simplify_search_url(self):
        standardized = standardize_url(
            "http://groups.google.com/forum/#!searchin/keras-users/model"
        )
        self.assertEqual(standardized, "groups.google.com/forum/!searchin")

    def test_tigsource_forums_keep_topic_id(self):
        standardized = standardize_url("http://forums.tigsource.com/index.php?topic=100.0")
        self.assertEqual(standardized, "forums.tigsource.com/index.php?topic=100.0")

    def test_tigsource_forums_keep_board_id(self):
        standardized = standardize_url("http://forums.tigsource.com/index.php?board=20.0")
        self.assertEqual(standardized, "forums.tigsource.com/index.php?board=20.0")

    def test_tigsource_forums_preserve_search_query_parameter(self):
        standardized = standardize_url(
            "http://forums.tigsource.com/index.php?action=search2;params=PARAMS"
        )
        self.assertEqual(standardized, "forums.tigsource.com/index.php?action=search2")

    def test_experiment_site_is_reduced_to_its_domain(self):
        standardized = standardize_url("http://searchlogger.tutorons.com/long/path#with-fragment")
        self.assertEqual(standardized, "searchlogger.tutorons.com")

    def test_browser_pages_are_reduced_to_the_words_browser_page(self):
        standardized = standardize_url("about:preferences")
        self.assertEqual(standardized, "browser_page")

    def test_yahoo_redirect_link_reduced_to_standard_path(self):
        standardized = standardize_url("http://r.search.yahoo.com/_ylt=AwrTccsomething")
        self.assertEqual(standardized, "r.search.yahoo.com/_ylt=redirect")

    def test_stack_overflow_question_reduce_to_id_as_path(self):
        standardized = standardize_url("http://stackoverflow.com/questions/1000/long-name")
        self.assertEqual(standardized, "stackoverflow.com/questions/1000")

    def test_pages_viewed_as_source_gets_view_source_prepended(self):
        standardized = standardize_url("view-source:http://site.com")
        self.assertEqual(standardized, "view-source:site.com")

    def test_bluejeans_site_standardizes_to_bluejeans_domain(self):
        standardized = standardize_url("http://bluejeans.com/long-path#some-fragment")
        self.assertEqual(standardized, "bluejeans.com")
