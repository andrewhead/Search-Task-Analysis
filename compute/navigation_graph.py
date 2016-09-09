#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import itertools
from peewee import fn

from models import LocationVisit, NavigationVertex, NavigationEdge


logger = logging.getLogger('data')


class Vertex(object):
    '''
    A vertex in a graph of web navigation behavior.  Includes data of how often it was
    visited, and how much time was spent their.
    '''
    def __init__(self, page_type, occurrences=0, total_time=0, mean_time=0):
        self.page_type = page_type
        self.occurrences = occurrences
        self.total_time = total_time
        self.mean_time = mean_time


class Edge(object):
    '''
    An edge in a graph of web navigation behavior.  Includes data of how often this
    edge was taken between these two vertices, and the probability that it was taken
    relative to all edges from the source vertex.  This data has to be manually
    computed and inserted into this object.
    '''
    def __init__(self, source_vertex, target_vertex, occurrences=0, probability=0):
        self.source_vertex = source_vertex
        self.target_vertex = target_vertex
        self.occurrences = 0
        self.probability = probability


def compute_navigation_graph(page_type_lookup, concern_index=None):

    # Create a new index for this computation
    last_compute_index = NavigationVertex.select(
        fn.Max(NavigationVertex.compute_index)
    ).scalar() or 0
    compute_index = last_compute_index + 1

    # Fetch the set of visits for the most recently computed visits
    visit_compute_index = LocationVisit.select(fn.Max(LocationVisit.compute_index)).scalar()
    visits = LocationVisit.select().where(LocationVisit.compute_index == visit_compute_index)

    # If the user has provided a concern index that they want to compute the graph for,
    # then restrict navigation data to only that concern
    if concern_index is not None:
        visits = visits.where(LocationVisit.concern_index == concern_index)

    # Get the distinct participant IDs and concern indexes
    participant_ids = set([visit.user_id for visit in visits])
    concern_indexes = set([visit.concern_index for visit in visits])

    # The list of vertices needs to be populated with a start and end node.
    # All navigation behavior starts at the "Start" node, and ends at the "End" node
    vertices = {
        "Start": Vertex("Start", occurrences=1),
        "End": Vertex("End", occurrences=1),
    }
    edges = {}
    last_vertex = vertices["Start"]

    # Go through every concern for every participant.  For each page they visit,
    # increment the visits to the corresponding vertex.  For each transition from one
    # page to the next, increment the occurrence of a transition between two page types.
    for participant_id in participant_ids:
        for concern_index in concern_indexes:

            participant_concern_visits = visits.where(
                LocationVisit.user_id == participant_id,
                LocationVisit.concern_index == concern_index,
            ).order_by(LocationVisit.start.asc())

            for visit in participant_concern_visits:

                # Get the type of the page visited
                if visit.url in page_type_lookup:
                    url_info = page_type_lookup[visit.url]
                    page_type = url_info['main_type']
                    # If this is a redirect, then just skip it.  It's more important
                    # to link the URL before it to the link the redirect points to.
                    if url_info['redirect']:
                        continue
                else:
                    logger.warn(
                        "URL %s not in page type lookup.  Giving it 'Unknown' type", visit.url
                    )
                    page_type = "Unknown"

                # Add a new vertex for this page type if it doesn't exist
                if page_type not in vertices:
                    vertices[page_type] = Vertex(page_type)

                # Save that we have seen this page type one more time
                vertex = vertices[page_type]
                vertex.occurrences += 1

                # Add the time spent to the total time spent for this page type
                time_passed = visit.end - visit.start
                seconds = time_passed.seconds + (time_passed.microseconds / float(1000000))
                vertex.total_time += seconds

                # Connect an edge between the last page visited and this one
                if (last_vertex.page_type, vertex.page_type) not in edges:
                    edges[(last_vertex.page_type, vertex.page_type)] = Edge(last_vertex, vertex)
                edge = edges[(last_vertex.page_type, vertex.page_type)]
                edge.occurrences += 1

                # Redefine the last page so we know in the next iteration what was just visited.
                last_vertex = vertex

            # After each participant or each concern, connect from the last URL to the end vertex
            end_vertex = vertices['End']
            if (last_vertex.page_type, end_vertex.page_type) not in edges:
                edges[(last_vertex.page_type, end_vertex.page_type)] = Edge(last_vertex, end_vertex)
            edge = edges[(last_vertex.page_type, end_vertex.page_type)]
            edge.occurrences += 1

            # After each participant or each concern, we reset the last_page_type to "Start"
            last_vertex = vertices['Start']

    # Compute the mean time spent on each vertex
    for vertex in vertices.values():
        vertex.mean_time = vertex.total_time / float(vertex.occurrences)

    # Compute the transition probability for each edge leaving a vertex.
    # First, group all edges by their source vertex
    get_source_page_type = lambda (source_type, target_type): source_type
    sorted_edge_keys = sorted(edges.keys(), key=get_source_page_type)
    edge_groups = itertools.groupby(sorted_edge_keys, get_source_page_type)

    for _, edge_group in edge_groups:

        # Fetch those edges in the current group
        # (Thos in the current group share the same source.)
        edge_keys = [_ for _ in edge_group]
        group_edges = dict(filter(lambda (k, v): k in edge_keys, edges.items()))

        # Compute the probability of each edge being taken
        total_occurrences = sum([e.occurrences for e in group_edges.values()])
        for edge in group_edges.values():
            edge.probability = float(edge.occurrences) / total_occurrences

    # Save all vertices to the database
    vertex_models = {}
    for vertex in vertices.values():
        vertex_model = NavigationVertex.create(
            compute_index=compute_index,
            page_type=vertex.page_type,
            occurrences=vertex.occurrences,
            total_time=vertex.total_time,
            mean_time=vertex.mean_time,
        )
        # We store a dictionary from page type to vertex model so
        # we can look up these models when saving the edges.
        vertex_models[vertex.page_type] = vertex_model

    # Save all edges to the database
    for edge in edges.values():
        NavigationEdge.create(
            compute_index=compute_index,
            source_vertex=vertex_models[edge.source_vertex.page_type],
            target_vertex=vertex_models[edge.target_vertex.page_type],
            occurrences=edge.occurrences,
            probability=edge.probability,
        )


def main(concern_index, *args, **kwargs):
    compute_navigation_graph(concern_index)


def configure_parser(parser):
    parser.description = "Compute the vertices and edges of a graph that shows the types " +\
        "of pages that participants dwell on and how they get between them."
    parser.add_argument(
        "page_types_json_filename",
        help=(
            "Name of a JSON file that maps URLs to file types.  " +
            "The format of each row should be:" +
            "\"<url>\": {\"main_type\": \"<main type>\", \"types\": " +
            "[<list of all relevant types>]}"
        )
    )
    parser.add_argument(
        "--concern-index",
        help=(
            "Filter the computation to consider just one concern for all participants. " +
            "When not specified, navigation behavior is counted over all concerns."
        )
    )
