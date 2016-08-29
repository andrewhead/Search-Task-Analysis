#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from peewee import fn
import numpy as np

from dump import make_dump_filename
from models import NavigationVertex, NavigationEdge


logger = logging.getLogger('data')

# Constants for laying out and drawing the graph.
MINIMUM_FONT_SIZE = 9
MINIMUM_VERTEX_SIZE = .65
EDGE_PEN_WIDTH_PER_PROBABILITY = 14

# This determines how many of the frequent page types and transitions are shown.
# Modify these to either reduce clutter or to show more information.
PAGE_TYPE_PERCENTILE = 80
TRANSITION_PERCENTILE = 90


def main(compute_index, output_format, *args, **kwargs):

    # Attempt to import graph_tool, and share a helpful debugging message if it's not found.
    try:
        import graph_tool.all as gt
    except ImportError as e:
        print str(e)
        print '\n'.join([
            "",
            "ERROR: The \"graph_tool\" module could not be imported.",
            "Install the package and then point to it with PYTHONPATH.",
            "",
            "Details: graph-tool isn't required for most scripts in this repository.",
            "But it's needed to draw graphs in *this* script.  To download this",
            "package, see the download instructions on the graph-tool website:",
            "",
            "https://graph-tool.skewed.de/download",
            ""
            "Note: it's not enough to install \"graph_tool\" through pip.",
            "It relies on C++ libraries for accelerated graph routines.",
            "You'll have to use your system package manager or compile from scratch.",
            "",
        ])
        raise SystemExit

    # This is the graph that we'll construct
    graph = gt.Graph()

    # These data structures hold links to the vertices, edges, and their properties
    vertices = {}
    vertex_page_types = []
    vertex_total_times = []
    vertex_mean_times = []
    vertex_occurrences = []
    edge_occurrences = []
    edge_probabilities = []

    # Fetch the set of graph data from the round of computation that the caller wants,
    # or from the most recent graph if a version hasn't been provided.
    # Note that the compute_index should be the same for the vertex and edge data, so we
    # look it up using the same index.
    if compute_index is None:
        compute_index = NavigationVertex.select(fn.Max(NavigationVertex.compute_index)).scalar()
    vertex_models = NavigationVertex.select().where(NavigationVertex.compute_index == compute_index)
    edge_models = NavigationEdge.select().where(NavigationEdge.compute_index == compute_index)

    # Add vertices to graph and save vertex properties
    for vertex_model in vertex_models:
        vertex = graph.add_vertex()
        vertices[vertex_model.id] = vertex
        vertex_page_types.append(vertex_model.page_type)
        vertex_total_times.append(vertex_model.total_time)
        vertex_mean_times.append(vertex_model.mean_time)
        vertex_occurrences.append(vertex_model.occurrences)

    # Add edges to the graph and save their properties
    for edge_model in edge_models:
        graph.add_edge(
            # We look up vertices using the '_vertex_id' properties because this is already
            # retrieved in the fetched rows.  Note that if we want to look it up by
            # page type, this will require two extra queries to the database (one for
            # each vertex) for each edge added, which is very costly.
            vertices[edge_model.source_vertex_id],
            vertices[edge_model.target_vertex_id],
        )
        edge_occurrences.append(edge_model.occurrences)
        edge_probabilities.append(edge_model.probability)

    # Because we're using unicode literals, each of the "value types" need to be coerced
    # to a string explicitly before creating new properties.
    # When making labels, we take advantage of the fact that most page types only have one
    # space, and usually they should be split into two new lines if they have a space.
    split_page_type_names = [_.replace(' ', '\n') for _ in vertex_page_types]
    vertex_labels = graph.new_vertex_property(str("string"), vals=split_page_type_names)

    # Determine vertex size based on frequently they have occurred.
    # While larger size means more visits, the relationship isn't linear.
    # The "log" is necessary to make sure that the difference isn't too severe between vertices.
    # This was hand-tailored to just look good.
    vertex_occurrences_array = np.array(vertex_occurrences)
    vertex_size_array = np.log((vertex_occurrences_array * float(10)) / np.max(vertex_occurrences))
    small_vertex_indexes = vertex_size_array < MINIMUM_VERTEX_SIZE
    vertex_size_array[small_vertex_indexes] = MINIMUM_VERTEX_SIZE
    vertex_sizes = graph.new_vertex_property(str("float"), vals=vertex_size_array)

    # Compute the font sizes to scale with vertex size.
    # This was hand-tailored to just look good too.
    font_size_array = vertex_size_array * 10
    small_font_indexes = font_size_array < MINIMUM_FONT_SIZE
    font_size_array[small_font_indexes] = MINIMUM_FONT_SIZE
    vertex_font_sizes = graph.new_vertex_property(str("double"), vals=font_size_array)

    # Edge thickness is determined by how likely a participant was to follow that transition
    edge_widths = graph.new_edge_property(
        str("float"),
        [p * EDGE_PEN_WIDTH_PER_PROBABILITY for p in edge_probabilities],
    )

    # Show only the top most frequently visited page types
    vertex_occurrences_array = np.array(vertex_occurrences)
    is_vertex_frequent = vertex_occurrences_array >=\
        np.percentile(vertex_occurrences_array, PAGE_TYPE_PERCENTILE)
    vertex_filter = graph.new_vertex_property(str("boolean"), vals=is_vertex_frequent)
    graph.set_vertex_filter(vertex_filter)

    # Show only the top most taken transitions
    edge_occurrences_array = np.array(edge_occurrences)
    is_edge_frequent = edge_occurrences_array >=\
        np.percentile(edge_occurrences_array, TRANSITION_PERCENTILE)
    edge_filter = graph.new_edge_property(str("boolean"), vals=is_edge_frequent)
    graph.set_edge_filter(edge_filter)

    # Create a new filename for the output that includes the index of the version of
    # data that was used when drawing it.
    output_filename = make_dump_filename(
        __name__ + "_compute_index_" + str(compute_index),
        "." + output_format,
    )

    # Draw the graph
    gt.graphviz_draw(
        graph,
        size=(40, 20),          # resulting image should be about 40cm by 20cm (seems unreliable)
        overlap=False,          # nodes should not be drawn on top of each other
        elen=1.5,                 # edges should be ~2in. long
        vcolor="#ffffff",       # vertices are white
        penwidth=edge_widths,   # edge thickness
        vsize=vertex_sizes,     # vertex sizes
        # For reference about graphviz vertex and edge properties in the next
        # two dictionaries, see this page:
        # http://www.graphviz.org/doc/info/attrs.html
        vprops={
            'fontsize': vertex_font_sizes,  # size of labels
            'label': vertex_labels,         # text of labels
            'shape': 'circle',
            'fixedsize': 'shape',           # don't scale vertices to fit text (looks weird)
        },
        eprops={
            # Surprisingly, we have to explicitly set these arrow properties
            # to make sure taht edges appear with a direction
            'arrowhead': 'normal',
            'dir': 'forward',
            # Setting splines to true makes sure that if there are edges in both directions
            # between two vertices, both of them get drawn and they don't overlap.
            'splines': 'true',
        },
        output=output_filename,
        output_format=output_format,
    )


def configure_parser(parser):
    parser.description = "Draw most recently computed web navigation graph to show " +\
        "the pages participants frequently visited and how they traveled between them."
    parser.add_argument(
        "--compute-index",
        help=(
            "Draw the graph from the data with the specified compute_index. " +
            "This refers to a specific version of the graph computed from navigation data. " +
            "If not specified, a graph will be plotted for the most recent data."
        )
    )
    parser.add_argument(
        "--output-format",
        help=(
            "Name of the format of image that is saved.  Defaults to %(default)s. " +
            "'svg' and 'ps' are two scalable image formats.  Find a full list of formats " +
            "for the `output_format` argument to the `graphviz_draw` method in the graph-tool " +
            "documentation: " +
            "https://graph-tool.skewed.de/static/doc/draw.html#graph_tool.draw.graphviz_draw"
        ),
        default="png",
    )
