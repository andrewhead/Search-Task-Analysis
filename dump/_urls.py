#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from urlparse import urlparse
import re


logger = logging.getLogger('data')


def standardize_url(url):
    '''
    Standardize a URL.  This means reducing a URL to single unique URL that will
    be the same for all other URLs that point to the same content.
    In most cases, this means just removing query parameters and fragments.
    Though this behavior gets more complex for other pages.
    For example, fragments are needed to disambiguate between different forums
    on Google Groups.  This routine takes care of all of that logic.
    '''

    url_parsed = urlparse(url)
    scheme = url_parsed.scheme
    fragment = url_parsed.fragment
    query = url_parsed.query

    if scheme == "view-source":
        # If we are viewing source, the original scheme, domain, and path all get
        # shoved into the "path" (though the fragment and query remain separate).
        # Here we split out the domain and path again.
        page_url = url_parsed.path
        domain = "view-source:" + urlparse(page_url).netloc
        path = urlparse(page_url).path
    else:
        domain = url_parsed.netloc
        path = url_parsed.path

    domain_without_www = re.sub("^www\.", "", domain)

    # Preserve the query parameters that identify Panda3D topics and forums.
    if domain_without_www == "panda3d.org":

        # Note that even though a URL for a Panda3D topic might include both
        # a topic number and a forum number, a few tests on my part showed that
        # the forum number isn't actually needed.  The topic numbers
        # are probably unique and independent of forum number.
        if re.match("(/forums)?/viewtopic.php", path) and re.search(r"(^|&)t=", query):
            topic_id = re.search(r"(^|&)t=(\d+)", query).group(2)
            return domain_without_www + path + "?t=" + topic_id
        elif re.match("(/forums)?/viewforum.php", path) and re.search(r"(^|&)f=", query):
            forum_id = re.search(r"(^|&)f=(\d+)", query).group(2)
            return domain_without_www + path + "?f=" + forum_id
        elif path == "/showss.php" and re.search(r"(^|&)shot=", query):
            shot_name = re.search(r"(^|&)shot=([^&]+)", query).group(2)
            return domain_without_www + path + "?shot=" + shot_name

    elif domain_without_www == "youtube.com" and path == "/watch" and re.search(r"(^|&)v=", query):
        video_id = re.search(r"(^|&)v=(\w+)", query).group(2)
        return domain_without_www + path + "?v=" + video_id

    elif domain_without_www == "groups.google.com":

        # Convert all Google Groups forums and topics into their own URLs
        if re.search(r"^!topic/", fragment) or re.search(r"^!forum/", fragment):
            return domain_without_www + path + fragment

        # Coalesce all search anywhere on Google Groups into one URL
        if re.search(r"^!searchin", fragment):
            return domain_without_www + path + "!searchin"

    # Tigsource forums and topics all get their own URLs too
    # We do topics before forums in case topic pages also have a
    # forum ID as part of their query parameters
    elif domain_without_www == "forums.tigsource.com":
        if re.search(r"(^|&)topic=", query):
            topic_id = re.search(r"(^|&)topic=([0-9.]+)", query).group(2)
            return domain_without_www + path + "?topic=" + topic_id
        elif re.search(r"(^|&)board=", query):
            board_id = re.search(r"(^|&)board=([0-9.]+)", query).group(2)
            return domain_without_www + path + "?board=" + board_id
        elif re.search(r"(^|&)action=search2", query):
            return domain_without_www + path + "?action=search2"

    # r.search.yahoo.com links from this study tended to be redirects.  I expect
    # that they were encountered as someone clicked on a search result from Yahoo.
    # Here, we make all redirects just be one single URL.
    elif domain_without_www == "r.search.yahoo.com" and path.startswith("/_ylt="):
        return domain_without_www + "/_ylt=redirect"

    # Stack Overflow questions can be referred to by their number alone, and by their number
    # and a longer readable name, and after that there can be the ID of an answer.
    # We consider the all to be the same page.
    elif domain_without_www == "stackoverflow.com" and re.search(r"^/questions/\d+/", path):
        question_id = re.search(r"^/questions/(\d+)/", path).group(1)
        return domain_without_www + "/questions/" + question_id

    # If this is the experiment site, return just one domain.  This squashes all visits
    # to the experiment site into just one URL
    elif (domain_without_www == "searchlogger.tutorons.com" or
            domain_without_www == "bluejeans.com"):
        return domain_without_www

    # Squash all browser pages (new tabs, preferences pages, etc.) into one unique URL
    elif scheme == "about":
        return "browser_page"

    return domain_without_www + path
