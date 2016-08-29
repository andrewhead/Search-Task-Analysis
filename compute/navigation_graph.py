#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
import itertools
from peewee import fn

from models import LocationVisit, NavigationVertex, NavigationEdge
from dump._urls import get_label


logger = logging.getLogger('data')


def compute_navigation_graph(concern_index=None, label_function=get_label):
    '''
    `label_function` must take a URL as its argument and return a dictionary with these properties:
    * `name`: the name of the page type (string)
    * `project`: whether this URL belongs to the project's documentation (Boolean)
    * `target`: if this is a search page, what is its target? (string or None)
    * `domain`: the domain name of the URL (string)
    '''
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

    vertices = {}
    edges = {}
    last_page_type = None

    # Go through every concern for every participant.  For each page they visit,
    # increment the visits to a vertex.  For each transition from one page to the next,
    # increment the occurrence of a transition between two page types.
    for participant_id in participant_ids:
        for concern_index in concern_indexes:

            participant_concern_visits = visits.where(
                LocationVisit.user_id == participant_id,
                LocationVisit.concern_index == concern_index,
            )

            for visit in participant_concern_visits:

                # Get the type of the page visited
                page_label = label_function(visit.url)
                page_type = page_label['name'] if page_label is not None else 'Unclassified'

                # Add a new vertex for this page type if it doesn't exist
                if page_type not in vertices:
                    vertices[page_type] = {
                        'occurrences': 0,
                        'total_time': 0,
                    }

                # Save that we have seen this page type one more time
                vertices[page_type]['occurrences'] += 1

                # Add the time spent to the total time spent for this page type
                time_passed = visit.end - visit.start
                seconds = time_passed.seconds + (time_passed.microseconds / float(1000000))
                vertices[page_type]['total_time'] += seconds

                # Connect an edge between the last page visited and this one
                if last_page_type is not None:
                    if (last_page_type, page_type) not in edges:
                        edges[(last_page_type, page_type)] = {
                            'occurrences': 0,
                        }
                    edge_properties = edges[(last_page_type, page_type)]
                    edge_properties['occurrences'] += 1

                # Redefine the last page so we know in the next iteration what was just visited.
                last_page_type = page_type

            # After each participant or each concern, we reset the last_page_type
            # to `None` so that we only connect edges from a single task.
            last_page_type = None

    # Compute the mean time spent on each vertex
    for vertex, properties in vertices.items():
        properties['mean_time'] = properties['total_time'] / properties['occurrences']

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
        total_occurrences = sum([edge['occurrences'] for edge in group_edges.values()])
        for edge_key, properties in group_edges.items():
            properties['probability'] = float(properties['occurrences']) / total_occurrences

    # Save all vertices to the database
    vertex_models = {}
    for page_type, properties in vertices.items():
        vertex_model = NavigationVertex.create(
            compute_index=compute_index,
            page_type=page_type,
            occurrences=properties['occurrences'],
            total_time=properties['total_time'],
            mean_time=properties['mean_time'],
        )
        # We store a dictionary from page type to vertex model so
        # we can look up these models when saving the edges.
        vertex_models[page_type] = vertex_model

    # Save all edges to the database
    for (source_page_type, target_page_type), properties in edges.items():
        NavigationEdge.create(
            compute_index=compute_index,
            source_vertex=vertex_models[source_page_type],
            target_vertex=vertex_models[target_page_type],
            occurrences=properties['occurrences'],
            probability=properties['probability'],
        )


def main(concern_index, *args, **kwargs):
    compute_navigation_graph(concern_index)


def configure_parser(parser):
    parser.description = "Compute the vertices and edges of a graph that shows the types " +\
        "of pages that participants dwell on and how they get between them."
    parser.add_argument(
        "--concern-index",
        help=(
            "Filter the computation to consider just one concern for all participants. " +
            "When not specified, navigation behavior is counted over all concerns."
        )
    )
