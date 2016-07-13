#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import logging
from urlparse import urlparse
import re


logger = logging.getLogger('data')


'''
Labels to assign to URLs for later classification.
A label includes:
* a name (e.g., "Docs", "Forum", etc.)
* whether this source was developed and maintained by the project developers.  This is similar
  to whether a source is 'official' but also covers source code, etc.
* a set of patterns of URLs (each consisting of a domain and a path or list of paths)

Paths don't need the preceding '/'.
Paths for 'search' can optionally include a 'target' which suggests what is being
searched (e.g., forums, example projects, code, etc.)

The label is found based on the first matching pattern.
These are heuristically written based on the patterns we observe in the URLs,
and may not be fool-proof for the URLs.
'''
LABELS = [{
    # Our research site
    'name': "Experiment site",
    'project': False,
    'patterns': [{
        'domain': "searchlogger.tutorons.com",
        'path': r".*",
    }, {
        # Pages for our Firefox addon
        'domain': "github.com",
        'path': r"^andrewhead/Web-Navigation-Logger/",
    }, {
        'domain': "bluejeans.com",
        'path': r"^\d+/(browser)?$",
    }, {
        # Consent form
        'domain': "docs.google.com",
        'path': [
            r"^forms/d/e/1FAIpQLSfLYxrbjsTJ_90lSHAktD3P_uBQrMqk8GM3YInTD1CeQ6WbxQ/viewform$",
            r"^a/colorado.edu/forms/d/1eGcDUOCNbsBbFCnAi5Ccb3nkwFHRxwav2ibW6Nacc0U/formResponse$",
        ],
    }]
}, {
    # Official documentation for various projects
    # Right now, if something is on the right site, we group it into the official documentation.
    # In the future, we should separate out the following
    # * FAQs
    # * tutorials
    # * reference
    # * search
    # * contribution guides
    # * news / release notes
    # * comparison pages
    # * download pages
    # * contact info
    # * resource / tutorial list
    # * pages mostly for navigation (more links than content)
    'name': "Docs",
    'project': True,
    'patterns': [{
        'domain': "keras.io",
        'path': [
            r"^$",  # Home page
            r"^layers/",
            r"^models/",
            r"^activations/",
            r"^constraints/",
            r"^initializations/",
            r"^objectives/",
            r"^preprocessing/image/",
            r"^search\.html",  # search
            r"^visualization/",
            r"^getting-started/",  # note that this includes FAQ and reference
            r"^faq/",
        ]
    }, {
        'domain': "lasagne.readthedocs.io",
        'path': r"^en/latest/",
    }, {
        'domain': "nose.readthedocs.io",
        'path': [
            r"^en/latest/$",  # home page
            r"^en/latest/index\.html$",  # home page
            r"^en/latest/finding_tests\.html$",
            r"^en/latest/testing\.html$",
            r"^en/latest/usage\.html$",
            r"^en/latest/writing_tests\.html$",
            r"^en/latest/plugins/multiprocess\.html$",
            r"^en/latest/plugins/xunit\.html$",
            r"^en/latest/contributing\.html$",
            r"^en/latest/developing\.html$",
            r"^en/latest/news\.html$",
            r"^en/latest/search\.html$",  # search
            r"^en/latest/setuptools_integration\.html$",
        ],
    }, {
        'domain': "nose2.readthedocs.io",
        'path': [
            r"^en/latest/$",  # home page
            r"^en/latest/index\.html$",  # home page
            r"^en/latest/getting_started\.html$",
            r"^en/latest/configuration\.html$",
            r"^en/latest/plugins\.html$",
            r"^en/latest/usage\.html$",
            r"^en/stable/decorators\.html$",
            r"^en/stable/dev/event_reference\.html$",
            r"^en/stable/getting_started\.html$",
            r"^en/stable/tools\.html$",
            r"^en/stable/usage\.html$",
            r"^en/latest/plugins/junitxml\.html$",
            r"^en/latest/plugins/configuration\.html$",
            r"^en/latest/dev/contributing\.html$",
            r"^en/latest/dev/documenting_plugins\.html$",
            r"^en/latest/differences\.html$",
        ],
    }, {
        # In this one really weird case, a past version of the official docs
        # was saved as a PDF and hosted somewhere else.
        'domain': "research.cs.wisc.edu",
        'path': r"^graphics/Courses/559-f2007/wiki/pub/tutorials/tutPanda/pandaManual.pdf$",
    }, {
        'domain': "panda3d.org",
        'path': [
            "^$",  # home page
            "^documentation\.php$",
            "^manual/index\.php/Cheat_Sheets$",
            "^manual/index\.php/Choosing_a_Texture_Size$",
            "^manual/index\.php/Introduction_to_Panda3D$",
            "^manual/index\.php/Main_Page$",
            "^manual/index\.php/Starting_Panda3D$",
            "^manual/index\.php/A_Panda3D_Hello_World_Tutorial$",
            "^manual/index\.php/Actor_Animations$",
            "^manual/index\.php/Attaching_an_Object_to_a_Joint$",
            "^manual/index\.php/Loading_Actors_and_Animations$",
            "^manual/index\.php/Loading_Models$",
            "^manual/index\.php/Loading_the_Grassy_Scenery$",
            "^manual/index\.php/Models_and_Actors$",
            "^manual/index\.php/Multi-Part_Actors$",
            "^manual/index\.php/OnscreenText$",
            "^manual/index\.php/Physics$",
            "^manual/index\.php/Text_Fonts$",
            "^manual/index\.php/Text_Node$",
            "^manual/index\.php/Text_and_Image_Rendering$",
            "^manual/index\.php/Text_Fonts$",
            "^manual/index\.php/Introductory_Tutorials$",
            "^reference/(\d+\.\d+\.\d+/|devel)",
            "^community\.php$",
            "^download\.php$",  # includes download pages for platform and SDK
            "^download/panda3d-\d+\.\d+\.\d+/notes-\d+\.\d+\.\d+\.txt$",
            "^manual/index\.php/The_IRC_Channel$",
            "^legal.php$",
            "^manual/index\.php/User_Contributed_Tutorials_and_Examples$",  # resource listing
            "^manual/index\.php/Video_Tutorials$",  # resource listing
            "^reference/python$",
        ],
    }, {
        'domain': "pygame.org",
        'path': [
            r"^hifi\.html$",  # home page
            r"^docs/",
            r"^readme\.html$",
            r"^wiki/",
            r"^download\.shtml$",
            r"^news\.html$",
        ],
    }, {
        'domain': "pytest.org",
        'path': [
            r"^latest/$",  # home page
            r"^latest/index\.html$",  # home page
            r"^latest/contents\.html$",
            r"^latest/overview\.html$",
            r"^latest/assert\.html$",
            r"^latest/example/$",
            r"^latest/example/nonpython\.html$",
            r"^latest/example/reportingdemo\.html$",
            r"^latest/fixture\.html$",
            r"^latest/getting-started\.html$",
            r"^latest/goodpractices\.html$",
            r"^latest/mark\.html$",
            r"^latest/nose\.html$",
            r"^latest/recwarn\.html$",
            r"^latest/skipping\.html$",
            r"^latest/unittest\.html$",
            r"^latest/usage\.html$",
            r"^latest/writing_plugins\.html$",
            r"^latest/xdist\.html$",
            r"^\d+\.\d+\.\d+(\.dev\d+)?/skipping\.html$",
            r"^latest/pytest\.pdf$",
            r"^latest/announce/index\.html$",
            r"^latest/announce/sprint2016\.html$",
            r"^latest/announce/release-\d+\.\d+\.\d+\.html$",
            r"^latest/changelog\.html$",
            r"^latest/contact\.html$",
            r"^latest/faq\.html$",
            r"^latest/search\.html$",  # search
            r"^latest/talks\.html$",
        ],
    }]
}, {
    # Docs for other packages / languages
    # See notes above for official docs about how we currently lump together
    # documentation that serves many different purposes.
    'name': "Docs",
    'project': False,
    'patterns': [{
        'domain': "django-nose.readthedocs.io",
        'path': r"^en/latest/",
    }, {
        'domain': "pytest-django.readthedocs.io",
        'path': [
            r"^en/latest/$",  # home page
            r"^en/latest/tutorial.html$",  # home page
            r"^en/latest/usage.html$",  # home page
            r"^en/latest/_sources/usage.txt$",
        ],
    }, {
        'domain': "deeplearning.net",
        'path': r"^software/theano/$",
    }, {
        'domain': "docs.python.org",
        'path': [
            r"^dev/library",
            r"^3/faq/$",
            r"^3/faq/library\.html$",
            r"^3/library/unittest\.html$",
        ]
    }, {
        'domain': "media.readthedocs.org",
        'path': r"^pdf/blenderpanda/latest/blenderpanda\.pdf$",
    }, {
        'domain': "python.org",
        'path': r"^doc/$"
    }, {
        'domain': "wiki.python.org",
        'path': [
            r"^moin/PyTest$",
            r"^moin/GameProgramming$",
        ]
    }, {
        'domain': "python.org",
        'path': [
            r"^$",
            r"^community/$",
        ]
    }]
}, {
    # Forums
    # TODO: differentiate between official and unofficial for forums
    'name': "Forum topic",
    'project': True,
    'patterns': [{
        'domain': "panda3d.org",
        'path': r"^forums/viewtopic.php$",
    }, {
        'domain': "groups.google.com",
        'path': r"^forum/",
        'fragment': r"!topic/[^/]+/[^/]+$",
    }, {
        'domain': "reddit.com",
        'path': r"^r/[^/]+/comments/[a-z0-9]{6}/[^/]+/$",
    }]
}, {
    'name': "Forum topic",
    'project': False,
    'patterns': [{
        'domain': "kaggle.com",
        'path': r"^forums/f/\d+/[^/]+/t/\d+/[^/]+/\d+$",
    }, {
        'domain': "forums.tigsource.com",
        'path': r"^index.php$",
        'query': r"topic=",
    }]
}, {
    'name': "Forum",
    'project': True,
    'patterns': [{
        'domain': "panda3d.org",
        'path': "^forums/viewforum\.php$",
    }, {
        'domain': "groups.google.com",
        'path': r"^forum/",
        'fragment': r"!forum/[^/]+$",
    }]
}, {
    'name': "Forum",
    'project': False,
    'patterns': [{
        'domain': "forums.tigsource.com",
        'path': r"^index.php$",
        'query': r"board=",
    }, {
        'domain': "reddit.com",
        'path': [
            r"^r/[^/]+/?$",
            # The following are different filters on the forum overview
            # This is kind of like search, but we're not categorizing it as such yet.
            r"^r/[^/]+/gilded/$",
            r"^r/[^/]+/top/$",
        ]
    }]
}, {
    'name': "Forum new post",
    'project': True,
    'patterns': [{
        'domain': "panda3d.org",
        'path': "^forums/posting.php$",
    }]
}, {
    'name': "Forum overview",
    'project': True,
    'patterns': [{
        'domain': "panda3d.org",
        'path': [
            "^forums/$",
            "^forums/index\.php$",
        ]
    }]
}, {
    'name': "Forum overview",
    'project': False,
    'patterns': [{
        'domain': "forums.tigsource.com",
        'path': r"^$",
    }]
}, {
    # Chat
    # TODO: check on whether it belongs to the project
    'name': "Chat",
    'project': True,
    'patterns': [{
        'domain': "kiwiirc.com",
        'path': r"^client/irc\.freenode\.net/$",
        'fragment': r"lasagne",
    }]
}, {
    # Q&A Sites
    # Note that while we group this all as "non-project" documentation, this might
    # not necessarily be true.  Some projects try to migrate a lot of communication
    # onto Stack Overflow, and advertise their tag on their main site.
    # This includes both sites for technical and non-technical Q&A (e.g., Stack Overflow vs. Quora)
    'name': "Q&A home",
    'project': False,
    'patterns': [{
        'domain': "stackoverflow.com",
        'path': r"^$",
    }, {
        'domain': "stackexchange.com",
        'path': r"^$",
    }]
}, {
    'name': "Q&A question",
    'project': False,
    'patterns': [{
        'domain': "stackoverflow.com",
        'path': r"^questions/\d+/",
    }, {
        'domain': "datascience.stackexchange.com",
        'path': r"^questions/\d+/",
    }, {
        'domain': "quora.com",
        'path': r"^[A-Z][^/]+$",
    }, {
        'domain': "gamedev.stackexchange.com",
        'path': r"^questions/\d+/"
    }]
}, {
    'name': "Discussion (miscellaneous)",
    'project': True,
    'patterns': [{
        'domain': "pygame.org",
        'path': "^project_comments\.html$"
    }, {
        'domain': "news.ycombinator.com",
        'path': r"^item$",
    }]
}, {
    # Search engines and interfaces
    'name': "Search home",
    'project': False,
    'patterns': [{
        'domain': "google.com",
        'path': r"^$",
    }, {
        'domain': "duckduckgo.com",
        'path': r"^$",
    }]
}, {
    'name': "Search home",
    'project': False,
    'patterns': [{
        'domain': "search.gmane.org",
        'path': r"^$",
    }]
}, {
    'name': "Search results",
    'project': False,
    'patterns': [{
        'domain': "google.com",
        'path': r"^search$",
    }, {
        'domain': "google.com",
        'path': r"^$",
        'fragment': r"^q=",  # query can be given as fragment
    }, {
        'domain': "encrypted.google.com",
        'path': r"^search$",
    }, {
        'domain': "google.co.uk",  # Google UK
        'path': r"^search$",
    }, {
        'domain': "search.yahoo.com",
        'path': r"^yhs/search$",
    }, {
        'domain': "duckduckgo.com",
        'path': r".*",
        'query': "^q=",
    }]
}, {
    # Search on various sites (official and unofficial)
    'name': "Search",
    'project': True,
    'patterns': [{
        'target': "site",
        'domain': "pygame.org",
        'path': [
            # I think participants only arrived at this search by mistake
            # It shows up in Google results when you search for Pygame forums
            "^tags/forum$",
            "^tags/example$",
        ]
    }, {
        # TODO: need to make sure URLs are official
        'target': 'forum',
        'domain': "groups.google.com",
        'path': r"^forum/",
        'fragment': r"!searchin/[^/]+/[^/]+/[^/]+/\w+/\w+$",
    }, {
        'target': "forum",
        'domain': "panda3d.org",
        'path': r"^forums/search.php$",
    }, {
        # TODO: need to make sure URLs are official
        'target': "code hosting project",
        'domain': "github.com",
        'path': r"^[^/]+/[^/]+/search$",
    }]
}, {
    # This search includes both for specific terms and within categories.
    'name': "Search",
    'project': False,
    'patterns': [{
        'target': "Q&A",
        'domain': "stackoverflow.com",
        'path': [
            r"^search$",
            r"^questions/tagged/[^/]+$",
            r"^unanswered/tagged/[^/]+$",
        ],
    }, {
        'target': "Q&A",
        'domain': "quora.com",
        'path': [
            r"^search$",
            r"^topic/[^/]+$",
        ]
    }, {
        'target': "forum",
        'domain': "reddit.com",
        'path': r"^r/[^/]+/search$",
    }, {
        'target': "forum",
        'domain': "forums.tigsource.com",
        'path': r"^index.php$",
        'query': r"action=search2",
    }, {
        'target': "package index",
        'domain': "pypi.python.org",
        'path': "^pypi$",
        'query': r"action=search",
    }, {
        'target': "video",
        'domain': "youtube.com",
        'path': "results$",
        'query': "search_query=",
    }]
}, {
    # Code hosting sites: Lot's of types of pages!
    # TODO: split into project and non-project repositories
    'name': "Code hosting home",
    'project': False,
    'patterns': [{
        'domain': "github.com",
        'path': r"^$",
    }]
}, {
    'name': "Issue overview",
    'project': True,
    'patterns': [{
        'domain': "github.com",
        'path': r"issues$",
    }, {
        'domain': "bugs.launchpad.net",
        'path': [
            r"^[^/]+$",
            r"^[^/]+/\+bugs$",
        ],
    }, {
        'domain': "bitbucket.org",
        'path': r"^[^/]+/[^/]+/issues$",
    }]
}, {
    'name': "Issue",
    'project': True,
    'patterns': [{
        'domain': "github.com",
        'path': r"issues/\d+$",
    }, {
        'domain': "bitbucket.org",
        'path': r"^[^/]+/[^/]+/issues/\d+(/[^/]+)?$",
    }, {
        'domain': "bugs.launchpad.net",
        'path': r"^[^/]+/\+bug/\d+$",
    }]
}, {
    'name': "Pull request overview",
    'project': True,
    'patterns': [{
        'domain': "github.com",
        'path': r"pulls$",
    }]
}, {
    'name': "Pull request",
    'project': True,
    'patterns': [{
        'domain': "github.com",
        'path': [
            r"pull/\d+$",
            r"pull/\d+/files$",
        ]
    }]
}, {
    'name': "Code hosting project home",
    'project': True,
    'patterns': [{
        'domain': "github.com",
        'path': r"^[^/]+/[^/]+/?$",
    }, {
        'domain': "bitbucket.org",
        'path': r"^[^/]+/[^/]+/?$",
    }]
}, {
    'name': "Commit history",
    'project': True,
    # Note that on GitHub a query can filter this list of commits
    'patterns': [{
        'domain': "github.com",
        'path': r"commits(/master(/.+)?)?",
    }, {
        'domain': "bitbucket.org",
        'path': r"[^/]+/[^/]+/commits/all$",
    }]
}, {
    'name': "Commit",
    'project': True,
    'patterns': [{
        'domain': "github.com",
        'path': r"commit/[a-f0-9]{40}$"
    }, {
        'domain': "bitbucket.org",
        'path': r"^[^/]+/[^/]+/commits/[a-f0-9]{40}$",
    }]
}, {
    'name': "Release history",
    'project': True,
    'patterns': [{
        'domain': "github.com",
        'path': r"releases$",
    }]
}, {
    'name': "Milestone",
    'project': True,
    'patterns': [{
        'domain': "github.com",
        'path': r"^[^/]+/[^/]+/milestones/[^/]+$",
    }]
}, {
    'name': "Project 'pulse'",
    'project': True,
    'patterns': [{
        'domain': "github.com",
        'path': [
            r"^[^/]+/[^/]+/pulse$",
            r"^[^/]+/[^/]+/pulse/monthly$",
        ]
    }]
}, {
    'name': "Contribution graph",
    'project': True,
    'patterns': [{
        'domain': "github.com",
        'path': [
            r"^[^/]+/[^/]+/graphs/contributors$",
            r"^[^/]+/[^/]+/graphs/code-frequency$",
        ]
    }]
}, {
    'name': "Network members",
    'project': True,
    'patterns': [{
        'domain': "github.com",
        'path': r"^[^/]+/[^/]+/network/members$",
    }]
}, {
    'name': "Wiki",
    'project': True,
    'patterns': [{
        'domain': "github.com",
        'path': [
            r"^[^/]+/[^/]+/wiki$",
            r"^[^/]+/[^/]+/wiki/([^_/][^/]*/)*[^_/][^/]*$",  # no underscores allowed in path.
                                                             # don't detect revision comparisons.
        ],
    }]
}, {
    'name': "Wiki revisions",
    'project': True,
    'patterns': [{
        'domain': "github.com",
        'path': r"^[^/]+/[^/]+/wiki/([^/]+/)*_compare",
    }]
}, {
    'name': "Source code",
    'project': True,
    'patterns': [{
        'domain': "github.com",
        'path': [
            r"^[^/]+/[^/]+/blob/",
            r"^[^/]+/[^/]+/tree/",
        ],
    }, {
        'domain': "bitbucket.org",
        'path': [
            r"^[^/]+/[^/]+/src$",
        ],
    }]
}, {
    'name': "Source code",
    'project': False,
    'patterns': [{
        'domain': "gist.github.com",
        'path': r"^[^/]+/[a-f0-9]{20}$",
    }]
}, {
    'name': "Downloads",
    'project': True,
    'patterns': [{
        'domain': "bitbucket.org",
        'path': r"^[^/]+/[^/]+/downloads$",
    }]
}, {
    # Tutorial sites and pages.
    # Although blog posts may include tutorials, these tutorials are posted
    # either on a tutorial portal, or somewhere that's 'not a blog'.
    # This can include online books.
    # Note that not all of these tutorials describe how to use a package.
    # Some of them focus on generic methods.  For example, the first Tuts+
    # tutorial describes test-driven development.
    'name': "Tutorial",
    'project': False,
    'patterns': [{
        'domain': "code.tutsplus.com",
        'path': r"^tutorials/",
    }, {
        'domain': "gamedevelopment.tutsplus.com",
        'path': r"^tutorials/[^/]+$",
    }, {
        'domain': "colinraffel.com",
        'path': r"^talks/next2015lasagne.pdf",
    }, {
        'domain': "halfcooked.com",
        'path': r"^presentations/pyconau2013/why_I_use_pytest.html$",
    }, {
        'domain': "ivory.idyll.org",
        'path': r"^articles/nose-intro.html$",
    }, {
        'domain': "programarcadegames.com",
        'path': r"^index.php$",
        'query': r"chapter=",
    }, {
        'domain': "teckla.idyll.org",
        'path': r"^~t/transfer/py\.test\.html$",
    }, {
        'domain': "docs.python-guide.org",
        'path': r"^en/latest/writing/tests/$",
    }, {
        'domain': "thepythongamebook.com",
        'path': r"^en:pygame:step\d\d\d$",
    }, {
        'domain': "zonca.github.io",
        'path': r"^2014-12-16-lbl/lecture_notes/testing/nose\.html$",
    }, {
        # This is a book preview, but includes some how-to content
        'domain': "leanpub.com",
        'path': r"^pythontesting/read$",
    }, {
        'domain': "guides.github.com",
        'path': r"^introduction/flow/$",
    }]
}, {
    # These are sites that link to pages of tutorial, but don't show
    # any one tutorial immediately on that page.
    'name': "Tutorial portal",
    'project': False,
    'patterns': [{
        'domain': "mygamefast.com",
        'path': r"^$",
    }, {
        'domain': "programarcadegames.com",
        'path': r"^$",
    }, {
        # Note that this page, while it has links to tutorial links pages, doesn't have any on it.
        'domain': "pygametutorials.wikidot.com",
        'path': r"^$",
    }, {
        'domain': "thepythongamebook.com",
        'path': "^en:pygame:start$"
    }]
}, {
    # This is when there's an ad or info page for a tutorial without the actual tutorial
    'name': "Tutorial description",
    'project': False,
    'patterns': [{
        'domain': "oreilly.com",
        'path': "^learning/[^/]+/purchase$",
    }, {
        'domain': "richard.cgpublisher.com",
        'path': "^product/pub\.84/prod\.11$",
    }],
}, {
    # Blog posts (official)
    'name': "Blog post",
    'project': True,
    'patterns': [{
        'domain': "blog.keras.io",
        'path': [
            r"^$",           # home page shows a blog entry
            r"[^/]*\.html",  # all HTML pages I can see by navigating the blog are blog posts
        ],
    }, {
        # TODO this should also be tagged as release information
        'domain': "panda3d.org",
        'path': [
            r"^blog/$",
            r"^blog/[^/]+/$",
        ],
    }],
}, {
    # Blog posts (unofficial)
    # While most of these are tutorials, not all of them are.  Some of them are just
    # introductions to libraries.
    # Blogs can belong to companies (e.g. Track Maven's "The Engine Room") or individuals.
    # In the case of "Python Testing", they can be affiliated with a book.
    'name': "Blog post",
    'project': False,
    'patterns': [{
        'domain': "machinelearningmastery.com",
        'path': [
            r"^tutorial-",
            r"^introduction-python-deep-learning-library-keras/$",
        ],
    }, {
        'domain': "agiletesting.blogspot.com",
        'path': r"^\d{4}/\d{2}/",
    }, {
        'domain': "blog.christianperone.com",
        'path': [
            r"^\d{4}/\d{2}/",
            r"^tag/",  # a tag search shows articles
        ],
    }, {
        'domain': "blog.krecan.net",
        'path': r"^\d{4}/\d{2}/\d{2}/",
    }, {
        'domain': "blog.jameskyle.org",
        'path': r"\d{4}/\d{2}/",
    }, {
        'domain': "danielnouri.org",
        'path': [
            r"^notes/\d{4}/\d{2}/\d{2}/[^/]+/",
            r"^notes/category/[^/]+/",  # category search shows articles
        ],
    }, {
        'domain': "engineroom.trackmaven.com",
        'path': r"blog/[^/]+/$",
    }, {
        'domain': "ermaker.github.io",
        'path': "^blog/\d{4}/\d{2}/\d{2}/[^/]+\.html",
    }, {
        'domain': "mathieu.agopian.info",
        'path': "^$",
    }, {
        'domain': "ofai.at",
        'path': "^~jan.schlueter/$",
    }, {
        'domain': "pythontesting.net",
        'path': [
            "^framework/nose/nose-introduction/$",
            "^framework/pytest/pytest-introduction/$",
        ],
    }, {
        'domain': "reinout.vanrees.org",
        'path': r"^weblog/\d{4}/\d{2}/\d{2}/[^/]+\.html$",
    }, {
        'domain': "ajanicij.info",
        'path': r"^content/pytest-tutorial$",
    }, {
        'domain': "gamedev.net",
        'path': r"^page/resources/_/technical/mobile-development/from-python-to-android-r3134$",
    }, {
        'domain': "ianbicking.org",
        'path': r"^pytest.html$",
    }, {
        'domain': "marekrei.com",
        'path': r"^blog/[^/]+/$",
    }, {
        'domain': "petercollingridge.co.uk",
        'path': r"^pygame-3d-graphics-tutorial$",
    }, {
        'domain': "pydanny.com",
        'path': r"^pytest-no-boilerplate-testing\.html$",
    }, {
        'domain': "grzegorzgwardys.wordpress.com",
        'path': r"^\d{4}/\d{2}/\d{2}/[^/]+/$",
    }, {
        'domain': "holgerkrekel.net",
        'path': r"^$",
    }, {
        'domain': "lorenzod8n.wordpress.com",
        'path': r"^\d{4}/\d{2}/\d{2}/[^/]+/$",
    }, {
        'domain': "martin-thoma.com",
        'path': r"^lasagne-for-python-newbies/$",
    }, {
        'domain': "swarbrickjones.wordpress.com",
        'path': r"^\d{4}/\d{2}/\d{2}/[^/]+/$",
    }, {
        'domain': "linuxsimba.com",
        'path': r"^mock_time_nose$",
    }, {
        'domain': "programeveryday.com",
        'path': r"^post/[^/]+/$",
    }, {
        'domain': "learningpython.com",
        'path': r"^\d{4}/\d{2}/\d{2}/[^/]+/$"
    }, {
        'domain': "metaklass.org",
        'path': "^nose-making-your-python-tests-smell-better/$",
    }, {
        'domain': "nerdparadise.com",
        'path': "^tech/python/pygame/basics/part1/$",
    }, {
        'domain': "realpython.com",
        'path': "^blog/python/pygame-a-primer/$",
    }, {
        'domain': "tigsource.com",
        'path': "^$",
    }]
}, {
    # Blog pages that aren't posts
    'name': "Blog miscellaneous",
    'project': False,
    'patterns': [{
        'domain': "ermaker.github.io",
        'path': r"^blog/$",  # this home page doesn't show articles
    }]
}, {
    # Developer and organization profiles
    'name': "Developer profile",
    'project': False,
    'patterns': [{
        'domain': "github.com",
        'path': r"^[^/]+$"
    }, {
        'domain': "stackoverflow.com",
        'path': r"^cv/[^/]+$",
    }, {
        # This one's only roughly a developer profile, as it's really just
        # an avatar that can be saved in different places.  It might not tell
        # you very much about the developer.
        'domain': "en.gravatar.com",
        'path': r"[a-z0-9]+$",
    }]
}, {
    # TODO: check on official group patterns
    'name': "Group profile",
    'project': True,
    'patterns': [{
        'domain': "plus.google.com",
        'path': r"^communities/\d+$",
    }]
}, {
    'name': "Group people",
    'project': False,
    'patterns': [{
        'domain': "github.com",
        'path': r"^orgs/[^/]+/people$",
    }]
}, {
    # Example projects
    # This includes both past projects that other have made for their own purposes,
    # and ones posted by the documentation writers to show the package's capabilities.
    'name': "Example project",
    'project': True,
    'patterns': [{
        'domain': "pygame.org",
        'path': [
            "^project-.*\.html$",
            # Note that there are comments on example projects
            # Tons of online entities today are socially enabled!
            "^project/\d+/$",
            # This one is just screenshots of example projects.
            "^screenshots\.html$",
        ]
    }, {
        # Note that these examples are playable!  Though that's only if you have the Panda3D
        # plugin, which I doubt folks who are evaluating this software will inspect.
        'domain': "panda3d.org",
        'path': [
            "^gallery/demo\.php$",
            "^manual/index\.php/Sample_Programs:_\w+$",
        ]
    }],
}, {
    'name': "Example project overview",
    'project': True,
    'patterns': [{
        'domain': "panda3d.org",
        'path': [
            "^manual/index\.php/Sample_Programs_in_the_Distribution$",
            "^gallery.php$",
            "^gallery/$",
        ]
    }]
}, {
    'name': "Example project overview",
    'project': False,
    'patterns': [{
        # Not sure if this site actually has examples made with Pygame, but I think that the
        # participant found the site when they were looking for Pygame examples.
        'domain': "pyweek.org",
        'path': [
            "^$",
            "^challenges/$",
        ]
    }]
}, {
    # Mailing lists
    # TODO: categorize this by official and unofficial
    'name': "Mailing list miscellaneous",
    'project': True,
    'patterns': [{
        'domain': "mail.python.org",
        'path': r"^mailman/listinfo/[^/]+$",
    }, {
        # This site has an interesting cue: a graph of the messages / day since Jan. 2005
        'domain': "dir.gmane.org",
        'path': "^gmane\.comp\.python\.pygame$",
    }]
}, {
    'name': "Mailing list navigation",
    'project': True,
    'patterns': [{
        'domain': "mail.python.org",
        'path': [
            r"^pipermail/[^/]+/$",
            r"^pipermail/[^/]+/\d{4}-[A-Z][a-z]+/thread\.html$",
        ],
    }]
}, {
    'name': "Mailing list thread / message",
    'project': True,
    'patterns': [{
        'domain': "mail.python.org",
        'path': r"^pipermail/[^/]+/\d{4}-[A-Z][a-z]+/\d+\.html$",
    }, {
        'domain': "lists.idyll.org",
        'path': "^pipermail/[^/]+/\d{4}-[A-Z][a-z]+/\d+\.html$",
    }, {
        # This site shows threads, but also shows a navigation interface through threads.
        # This is one that really needs to be classified as two.
        'domain': "news.gmane.org",
        'path': "^gmane.comp.python.pygame$",
    }]
}, {
    'name': "Mailing list thread / message",
    'project': False,
    'patterns': [{
        'domain': "lists.debian.org",
        'path': "^debian-python/\d{4}/\d{2}/msg\d{5}\.html$",
    }]
}, {
    # News sites
    'name': "News home",
    'project': False,
    'patterns': [{
        'domain': "arstechnica.com",
        'path': r"^$",
    }, {
        'domain': "limitsizandroid.com",
        'path': r"^$",
    }]
}, {
    # Wikipedia
    'name': "Wikipedia",
    'project': False,
    'patterns': [{
        'domain': "en.wikipedia.org",
        'path': r"^wiki/[^/]+$",
    }]
}, {
    # Package indexes
    # With package indexes, the line between whether this is built by the project
    # or not starts to get fuzzy.  Projects can add metadata and READMEs that determine
    # how their package's entry will appear.  But the design of the page and a lot of
    # the other metadata will be produced by the site.  And some authors don't really
    # take effort to design their packages' appearance for all sites
    # For the time being, we consider this not to be project documentation.
    # We group together all pages on package indexes (detail and overview)
    'name': "Package index",
    'project': False,
    'patterns': [{
        'domain': "packages.tanglu.org",
        'path': r"^en/staging/[^/]+$",
    }, {
        'domain': "pypi.python.org",
        'path': [
            r"^pypi/[^/]+(/[^/]+)?$",  # optional version number
            r"^pypi/[^/]+/$",  # overview of versions
        ]
    }]
}, {
    # Comparison sites
    'name': "Package comparison",
    'project': False,
    'patterns': [{
        'domain': "python.libhunt.com",
        'path': r"^project/[^/]+/vs/[^/]+$",
    }]
}, {
    # Package review sites
    'name': "Package review",
    'project': False,
    'patterns': [{
        'domain': "slant.co",
        'path': r"^options/\d+/~[^/]+-review$",
    }]
}, {
    # Compatability testers
    'name': "Plugin compatibility",
    'project': True,  # created by the pytest-dev team
    'patterns': [{
        'domain': "plugincompat.herokuapp.com",
        'path': r"^$",
    }]
}, {
    # Build test sites
    # TODO differentiate between project and not
    'name': "Build and integration",
    'project': True,
    'patterns': [{
        'domain': "ci.appveyor.com",
        'path': [
            r"^project/[^/]+/[^/]+$",
            r"^project/[^/]+/[^/]+/history$",
        ],
    }, {
        'domain': "travis-ci.org",
        'path': r"^[^/]+/[^/]+$",
    }]
}, {
    # Videos
    'name': "Video",
    'project': False,
    'patterns': [{
        'domain': "youtube.com",
        'path': r"^watch$",
        'query': r"^v=",
    }],
}, {
    # Podcasts
    'name': "Podcast",
    'project': False,
    'patterns': [{
        'domain': "pythontesting.net",
        'path': r"^podcast/[^/]+/$",
    }]
}, {
    # Miscellaneous: things that aren't worth classifying yet
    'name': "Miscellaneous",
    'project': False,
    'patterns': [{
        # Course material
        'domain': "cs231n.github.io",
        'path': [
            r"^$",
            r"^assignments\d{4}/assignment\d+/$",
        ],
    }, {
        # Documentation engine
        'domain': "sphinx-doc.org",
        'path': r"^en/stable/$",
    }, {
        # Documentation hosting
        'domain': "readthedocs.org",
        'path': [
            r"^$",
            r"^projects/lasagne/$",
        ]
    }, {
        # SEO pages for web sites
        'domain': "seoceros.com",
        'path': "^en/lasagne.ml$",  # note that this is for an irrelevant page
    }, {
        'domain': "compare.easycounter.com",
        'path': "^[^/]+-vs-[^/]+$",
    }, {
        # Poster for academic project
        'domain': "cs.nmsu.edu",
        'path': "^~kvillave/papers/Karen6T.pdf$",
    }, {
        # Presentations
        # Although some blog posts are summaries of presentations, if they have
        # been reformatted to look like a blog post, we include it in "blogs" above.
        'domain': "mathieu.agopian.info",
        'path': "^presentations/2015_06_djangocon_europe/$",
    }, {
        # Participant was visiting GMail
        'domain': "mail.google.com",
        'path': ".*",
    }, {
        # YouTube is a general enough site that we can't make much of a participant's
        # purpose when they go to look at YouTube
        'domain': "youtube.com",
        'path': "^$",
    }]
}, {
    # Missing: to my knowledge, these sites were not accessible to participants.
    # This is because the page is inaccessible when I try to view it, and when
    # I look on the Internet Archive for recent scrapes, a successful scrape is missing.
    'name': "Inaccessible",
    'project': None,  # these are neither official nor unofficial.  Just absent.
    'patterns': [{
        'domain': "codespeak.net",
        'path': r"^py/current/doc/test.html$",
    }, {
        'domain': "nose2.readthedocs.io",
        'path': r"^en/$",
    }, {
        'domain': "stackoverflow.com",
        'path': r"^tagged/[^/]+$",  # to my knowledge, this URL doesn't exist on Stack Overflow
    }, {
        'domain': "pygame.org",
        'path': r"^whatsnew\.shtml$",
    }, {
        'domain': "bigaidream.gitbooks.io",
        'path': r"^subsets_ml_cookbook/content/dl/theano/theano_lasagne_tutorial\.html$",
    }, {
        'domain': "crate.io",
        'path': r"^packages/nose2/$",
    }, {
        # This wasn't scraped by the Internet Archive, though I wasn't able to access it.
        'domain': "rdb.name",
        'path': r"^$",
    }, {
        'domain': "rene.f0o.com",
        'path': r"^mywiki/PythonGameProgramming$",
    }]
}, {
    # Redirects: these links just redirected us to another page when we accessed them.
    # So we won't consider them to be their own pages.
    # Note that Yahoo seems to provide redirects for at least some of the links one
    # selects from a search results page.
    'name': "Redirect",
    'project': None,  # we don't consider these to be fixations
    'patterns': [{
        'domain': "pythonhosted.org",
        'path': r"^nose/$",
    }, {
        'domain': "r.search.yahoo.com",
        'path': r".*",
    }, {
        'domain': "google.com",
        'path': r"^url$",
    }]
}]


def get_label(url):
    ''' Look up a descriptive label for what content is at the URL. '''

    url_parsed = urlparse(url)
    visit_scheme = url_parsed.scheme
    visit_domain = url_parsed.netloc
    visit_path = url_parsed.path
    visit_fragment = url_parsed.fragment
    visit_query = url_parsed.query

    # First, handle the strange case of a browser URL (like opening a new tab) or viewing source
    if visit_scheme == "about":
        return {
            'domain': None,
            'name': "Browser page",
            'project': None,
        }
    elif visit_scheme == "view-source":
        return {
            'domain': None,
            'name': "View page source",
            'project': None,
        }

    # Try to match the URL against all labels
    for label in LABELS:

        for pattern in label['patterns']:

            # Look for an exact domain match (no subdomains)
            if re.match("^(www\.)?" + pattern['domain'] + '$', visit_domain):

                # Handle path options that can be either a string or a list
                if isinstance(pattern['path'], str) or isinstance(pattern['path'], unicode):
                    path_options = [pattern['path']]
                elif isinstance(pattern['path'], list):
                    path_options = pattern['path']

                # Try to match the path against all provided patterns.
                # If a match is made, return the label found
                for path_option in path_options:

                    visit_path_without_slash = re.sub('^/', '', visit_path)
                    if re.search(path_option, visit_path_without_slash):

                        # We have found that some sites (like Google Groups)
                        # include fragments when addressing distinct types of pages
                        # (like topics and forums).  It can also include a query
                        # to change its content (see programarcadegames.com chapters).
                        # So a label can optionally include a rule to match a fragment
                        # or a query.  If no fragment or query is specified, then
                        # this matches by default
                        matches = True
                        if 'fragment' in pattern:
                            if not re.search(pattern['fragment'], visit_fragment):
                                matches = False
                        if 'query' in pattern:
                            if not re.search(pattern['query'], visit_query):
                                matches = False
                        if matches:
                            return {
                                'name': label['name'],
                                'project': label['project'],
                                'target': pattern.get('target'),
                                'domain': pattern['domain'],
                            }

    return None
