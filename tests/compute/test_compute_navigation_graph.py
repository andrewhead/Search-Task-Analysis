#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import datetime

from compute.navigation_graph import compute_navigation_graph
from tests.base import TestCase
from tests.modelfactory import create_location_visit
from models import LocationVisit, NavigationVertex, NavigationEdge


logger = logging.getLogger('data')


def label_url(url):
    if url == 'page1':
        page_type = "page_type_1"
    elif url == 'page2':
        page_type = "page_type_2"
    return {'name': page_type}


class ComputeLocationVisitsTest(TestCase):

    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(
            [LocationVisit, NavigationVertex, NavigationEdge],
            *args, **kwargs
        )

    def test_vertex_occurrences_count_visits_to_page_type(self):

        # Create a set of visits that a participant made to a few pages
        create_location_visit(
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
        )
        create_location_visit(
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 3, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 4, 0),
        )
        create_location_visit(
            url="page2",
            start=datetime.datetime(2000, 1, 1, 12, 0, 5, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 6, 0),
        )

        # Compute a navigation graph by inspecting the location visits one by one
        # We provide a "dummy" function that will assign a page type to each URL
        # that we can keep distinct from the typical page label function that's
        # likely to change in the near future.
        compute_navigation_graph(label_function=label_url)
        vertices = NavigationVertex.select()

        # Two vertices have been created, one for each page type
        self.assertEqual(vertices.count(), 2)
        page_type_1_vertex = vertices.where(NavigationVertex.page_type == "page_type_1").first()
        page_type_2_vertex = vertices.where(NavigationVertex.page_type == "page_type_2").first()
        self.assertEqual(page_type_1_vertex.occurrences, 2)
        self.assertEqual(page_type_2_vertex.occurrences, 1)

    def test_vertex_total_time_counts_time_of_all_visits(self):

        create_location_visit(
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),  # 1 second
        )
        create_location_visit(
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 3, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 6, 0),  # + 3 seconds = 4 seconds
        )
        create_location_visit(
            url="page2",
            start=datetime.datetime(2000, 1, 1, 12, 0, 5, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 6, 0),  # 1 second
        )

        compute_navigation_graph(label_function=label_url)
        vertices = NavigationVertex.select()
        page_type_1_vertex = vertices.where(NavigationVertex.page_type == "page_type_1").first()
        page_type_2_vertex = vertices.where(NavigationVertex.page_type == "page_type_2").first()

        self.assertEqual(page_type_1_vertex.total_time, 4)
        self.assertEqual(page_type_2_vertex.total_time, 1)

    def test_vertex_mean_time_averages_time_of_visits(self):

        create_location_visit(
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),  # 1 second
        )
        create_location_visit(
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 3, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 6, 0),  # + 3 seconds = 4 seconds (avg: 2s)
        )
        create_location_visit(
            url="page2",
            start=datetime.datetime(2000, 1, 1, 12, 0, 5, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 6, 0),  # 1 second (avg: 1s)
        )

        compute_navigation_graph(label_function=label_url)
        vertices = NavigationVertex.select()
        page_type_1_vertex = vertices.where(NavigationVertex.page_type == "page_type_1").first()
        page_type_2_vertex = vertices.where(NavigationVertex.page_type == "page_type_2").first()

        self.assertEqual(page_type_1_vertex.mean_time, 2)
        self.assertEqual(page_type_2_vertex.mean_time, 1)

    def test_edge_added_between_all_consecutive_visits(self):

        create_location_visit(
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
        )
        create_location_visit(
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 3, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 4, 0),
        )
        create_location_visit(
            url="page2",
            start=datetime.datetime(2000, 1, 1, 12, 0, 5, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 6, 0),
        )

        compute_navigation_graph(label_function=label_url)
        edges = NavigationEdge.select()
        self.assertEqual(edges.count(), 2)

        edge_page_type_pairs = [
            (edge.source_vertex.page_type, edge.target_vertex.page_type)
            for edge in edges
        ]
        self.assertIn(("page_type_1", "page_type_1"), edge_page_type_pairs)
        self.assertIn(("page_type_1", "page_type_2"), edge_page_type_pairs)

    def test_edge_occurrences_counts_number_of_transitions_between_page_types(self):

        create_location_visit(
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
        )
        create_location_visit(
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 3, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 4, 0),
        )
        create_location_visit(
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 5, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 6, 0),
        )
        create_location_visit(
            url="page2",
            start=datetime.datetime(2000, 1, 1, 12, 0, 7, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 8, 0),
        )

        compute_navigation_graph(label_function=label_url)
        edges = NavigationEdge.select()
        edge_dict = {
            (edge.source_vertex.page_type, edge.target_vertex.page_type): edge
            for edge in edges
        }
        self.assertEqual(edge_dict[('page_type_1', 'page_type_1')].occurrences, 2)
        self.assertEqual(edge_dict[('page_type_1', 'page_type_2')].occurrences, 1)

    def test_edge_transition_probabilities_normalize_occurrences(self):

        create_location_visit(
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
        )
        create_location_visit(
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 3, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 4, 0),
        )
        create_location_visit(
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 5, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 6, 0),
        )
        create_location_visit(
            url="page2",
            start=datetime.datetime(2000, 1, 1, 12, 0, 7, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 8, 0),
        )
        create_location_visit(
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 9, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 10, 0),
        )

        compute_navigation_graph(label_function=label_url)
        edges = NavigationEdge.select()
        edge_dict = {
            (edge.source_vertex.page_type, edge.target_vertex.page_type): edge
            for edge in edges
        }
        self.assertAlmostEqual(edge_dict[('page_type_1', 'page_type_1')].probability, float(2) / 3)
        self.assertAlmostEqual(edge_dict[('page_type_1', 'page_type_2')].probability, float(1) / 3)
        self.assertAlmostEqual(edge_dict[('page_type_2', 'page_type_1')].probability, 1)

    def test_edge_not_added_between_participants(self):

        create_location_visit(
            user_id=0,
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
        )
        create_location_visit(
            user_id=1,
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 3, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 4, 0),
        )

        compute_navigation_graph(label_function=label_url)
        self.assertEqual(NavigationEdge.select().count(), 0)

    def test_edge_not_added_between_concerns_for_the_same_participant(self):

        create_location_visit(
            concern_index=0,
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
        )
        create_location_visit(
            concern_index=1,
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 3, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 4, 0),
        )

        compute_navigation_graph(label_function=label_url)
        self.assertEqual(NavigationEdge.select().count(), 0)

    def test_graph_computation_uses_only_latest_computed_visits(self):

        create_location_visit(
            compute_index=0,
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
        )
        create_location_visit(
            compute_index=1,
            url="page2",
            start=datetime.datetime(2000, 1, 1, 12, 0, 3, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 4, 0),
        )
        create_location_visit(
            compute_index=1,
            url="page2",
            start=datetime.datetime(2000, 1, 1, 12, 0, 3, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 4, 0),
        )

        compute_navigation_graph(label_function=label_url)
        self.assertEqual(NavigationEdge.select().count(), 1)
        edge = NavigationEdge.select().first()
        self.assertEqual(edge.source_vertex.page_type, "page_type_2")
        self.assertEqual(edge.target_vertex.page_type, "page_type_2")

    def test_filter_to_only_one_concern_if_concern_index_provided(self):

        # This event should be ignored
        create_location_visit(
            concern_index=0,
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
        )
        create_location_visit(
            concern_index=0,
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 3, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 4, 0),
        )
        # This event should be captured
        create_location_visit(
            concern_index=1,
            url="page2",
            start=datetime.datetime(2000, 1, 1, 12, 0, 5, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 6, 0),
        )
        create_location_visit(
            concern_index=1,
            url="page2",
            start=datetime.datetime(2000, 1, 1, 12, 0, 7, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 8, 0),
        )

        compute_navigation_graph(concern_index=1, label_function=label_url)
        self.assertEqual(NavigationEdge.select().count(), 1)
        edge = NavigationEdge.select().first()
        self.assertEqual(edge.source_vertex.page_type, "page_type_2")
        self.assertEqual(edge.target_vertex.page_type, "page_type_2")

    def test_include_all_concerns_if_no_concern_index_provided(self):

        # Both events should be captured
        create_location_visit(
            concern_index=0,
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 1, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 2, 0),
        )
        create_location_visit(
            concern_index=0,
            url="page1",
            start=datetime.datetime(2000, 1, 1, 12, 0, 3, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 4, 0),
        )
        create_location_visit(
            concern_index=1,
            url="page2",
            start=datetime.datetime(2000, 1, 1, 12, 0, 5, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 6, 0),
        )
        create_location_visit(
            concern_index=1,
            url="page2",
            start=datetime.datetime(2000, 1, 1, 12, 0, 7, 0),
            end=datetime.datetime(2000, 1, 1, 12, 0, 8, 0),
        )

        compute_navigation_graph(label_function=label_url)
        self.assertEqual(NavigationEdge.select().count(), 2)
