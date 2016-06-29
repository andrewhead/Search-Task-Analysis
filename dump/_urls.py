#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from urlparse import urlparse
import re


logger = logging.getLogger('data')
DOMAINS = [
    {'domain': "stackoverflow.com", 'name': "Stack Overflow"},
    {'domain': "github.com", 'name': "GitHub"},
    {'domain': "reddit.com", 'name': "Reddit"},
    {'domain': "google.com", 'name': "Google"},
    {'domain': "keras.io", 'name': "Keras"},
    {'domain': "nose2.readthedocs.io", 'name': "Nose 2 docs"},
    {'domain': "nose.readthedocs.io", 'name': "Nose docs"},
    {'domain': "pytest.org", 'name': "PyTest"},
    {'domain': "lasagne.readthedocs.io", 'name': "Lasagne docs"},
    {'domain': "panda3d.org", 'name': "Panda3D"},
    {'domain': "pygame.org", 'name': "Pygame"},
]


def get_domain_name(url):
    ''' Look up the name of the domain for a URL. '''

    visit_domain = urlparse(url).netloc
    domain_name = 'Unknown'

    for domain in DOMAINS:

        # Allow each URL to match sub-domains and domains starting with 'www'
        if re.match('(www\.)?(.*\.)?' + domain['domain'] + '$', visit_domain):
            domain_name = domain['name']
            break

    return domain_name
