#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from urlparse import urlparse
import re


logger = logging.getLogger('data')


# Specify these from more specific to less specific.
# These patterns will be tried in the order that they appear here.
# So earlier rules should include subdomains, and later rules
# should include more generic "catch-all" domains.
DOMAINS = [
    {'domain': "stackoverflow.com", 'name': "Stack Overflow"},
    {'domain': "github.com", 'name': "GitHub"},
    {'domain': "reddit.com", 'name': "Reddit"},
    {'domain': "groups.google.com", 'name': "Google Groups"},
    {'domain': "google.com", 'name': "Google"},
    {'domain': "keras.io", 'name': "Keras"},
    {'domain': "nose2.readthedocs.io", 'name': "Nose 2 docs"},
    {'domain': "nose.readthedocs.io", 'name': "Nose docs"},
    {'domain': "pytest.org", 'name': "PyTest"},
    {'domain': "lasagne.readthedocs.io", 'name': "Lasagne docs"},
    {'domain': "panda3d.org", 'name': "Panda3D"},
    {'domain': "pygame.org", 'name': "Pygame"},
    {'domain': "searchlogger.tutorons.com", 'name': "Experiment site"},
]


# A label used to annotate more specifically what someone will find at a specific page.
# Each entry in this list comprises a domain where it is found and a pattern (or a list
# of patterns) that, when they match the path for the URL, tells us to label a
# URL with this label.  Paths don't need the preceding '/'.
# Note that for the time being, only one label can
# be assigned to each URL, and they will be tested in order.
#
# These are heuristically written based on the patterns we observe in the URLs,
# and may not be fool-proof for the URLs that the sites actually accept.
# Also, note that currently these labels are overfitted to a sample of data from S4.
LABELS = [{
    # Our research site
    'name': "Experiment site",
    'domain': "searchlogger.tutorons.com",
    'path': r".*",
}, {
    # Official documentation for various projects
    'name': "Lasagne official docs",
    'domain': "lasagne.readthedocs.io",
    'path': r"^en/latest/",
}, {
    'name': "Keras official docs",
    'domain': "keras.io",
    'path': [
        r"^layers/",
        r"^models/"
    ],
}, {
    # Google Groups
    'name': "Google Groups overview",
    'domain': "groups.google.com",
    'path': r"^forum/",
    'fragment': r"!forum/[^/]+$",
}, {
    'name': "Google Groups topic",
    'domain': "groups.google.com",
    'path': r"^forum/",
    'fragment': r"!topic/[^/]+/[^/]+$",
}, {
    # Google
    'name': "Google search",
    'domain': "google.com",
    'path': r"^search",
}, {
    # GitHub
    'name': "GitHub issue overview",
    'domain': "github.com",
    'path': r"issues$",
}, {
    'name': "GitHub issue",
    'domain': "github.com",
    'path': r"issues/\d+$",
}, {
    'name': "GitHub pull request overview",
    'domain': "github.com",
    'path': r"pulls$",
}, {
    'name': "GitHub project home",
    'domain': "github.com",
    'path': r"^[^/]+/[^/]+$",
}, {
    'name': "GitHub commit history",
    'domain': "github.com",
    'path': r"commits/master$",
}, {
    'name': "Example code",
    'domain': "github.com",
    'path': [
        r"^Lasagne/Lasagne/blob/master/examples/mnist.py$"
    ],
}, {
    # Stack Overflow
    'name': "Stack Overflow home",
    'domain': "stackoverflow.com",
    'path': r"^$",
}, {
    'name': "Stack Overflow search",
    'domain': "stackoverflow.com",
    'path': r"^questions/tagged/[^/]+$",
}, {
    'name': "Stack Overflow question",
    'domain': "stackoverflow.com",
    'path': r"^questions/\d+/",
}, {
    # Blog posts
    'name': "Blog: Machine Learning Mastery",
    'domain': "machinelearningmastery.com",
    'path': r"^tutorial-",
}]


def get_label(url):
    ''' Look up a descriptive label for what content is at the URL. '''

    url_parsed = urlparse(url)
    visit_scheme = url_parsed.scheme
    visit_domain = url_parsed.netloc
    visit_path = url_parsed.path
    visit_fragment = url_parsed.fragment

    # First, handle the strange case of a browser URL (like opening a new tab)
    if visit_scheme == "about":
        return "Browser page"

    # Try to match the URL against all labels
    for label in LABELS:

        # Look for an exact domain match (no subdomains)
        if re.match("^(www\.)?" + label['domain'] + '$', visit_domain):

            # Handle path options that can be either a string or a list
            if isinstance(label['path'], str) or isinstance(label['path'], unicode):
                path_options = [label['path']]
            elif isinstance(label['path'], list):
                path_options = label['path']

            # Try to match the path against all provided patterns.
            # If a match is made, return the label found
            for path_option in path_options:

                visit_path_without_slash = re.sub('^/', '', visit_path)
                if re.search(path_option, visit_path_without_slash):

                    # We have found that some sites (like Google Groups)
                    # include fragments when addressing distinct types of pages
                    # (like topics and forums).  So a label can optionally
                    # include a rule to match a fragment.
                    if 'fragment' in label:
                        if re.match(label['fragment'], visit_fragment):
                            return label['name']
                    # But if there's no fragment specified, then this is a match
                    else:
                        return label['name']

    return "Unclassified"


def get_domain_name(url):
    ''' Look up the name of the domain for a URL. '''

    visit_domain = urlparse(url).netloc
    domain_name = 'Unclassified'

    for domain in DOMAINS:

        # Allow each URL to match sub-domains and domains starting with 'www'
        if re.match('(www\.)?(.*\.)?' + domain['domain'] + '$', visit_domain):
            domain_name = domain['name']
            break

    return domain_name
