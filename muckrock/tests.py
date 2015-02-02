"""
Tests for site level functionality and helper functions for application tests
"""

from django.core.urlresolvers import reverse
from django.test import TestCase

import logging
import nose.tools

# allow methods that could be functions and too many public methods in tests and **kwarg magic
# pylint: disable=R0201
# pylint: disable=R0904
# pylint: disable=W0142

logging.disable(logging.CRITICAL)

kwargs = {"wsgi.url_scheme": "https"}

# helper functions for view testing
def get_allowed(client, url, templates=None, base='base.html', context=None, redirect=None):
    """Test a get on a url that is allowed with the users current credntials"""
    # pylint: disable=R0913
    response = client.get(url, follow=True, **kwargs)
    nose.tools.eq_(response.status_code, 200)

    if redirect:
        nose.tools.eq_(response.redirect_chain, [('https://testserver:80' + redirect, 302)])

    if templates:
        resp_ts = [t.name for t in response.templates[:len(templates)+1]]
        nose.tools.eq_(resp_ts, templates + [base])

    if context:
        for key, value in context.iteritems():
            nose.tools.eq_(response.context[key], value)

    return response

def post_allowed(client, url, data, redirect):
    """Test an allowed post with the given data and redirect location"""
    response = client.post(url, data, follow=True, **kwargs)
    nose.tools.eq_(response.status_code, 200)
    nose.tools.eq_(response.redirect_chain, [('https://testserver:80' + redirect, 302)])

    return response

def post_allowed_bad(client, url, templates, data=None):
    """Test an allowed post with bad data"""
    if data is None:
        data = {'bad': 'data'}
    response = client.post(url, data, **kwargs)
    nose.tools.eq_(response.status_code, 200)
    # make sure first 3 match (4th one might be form.html, not important
    nose.tools.eq_([t.name for t in response.templates][:3], templates + ['base.html'])

def get_post_unallowed(client, url):
    """Test an unauthenticated get and post on a url that is allowed
    to be viewed only by authenticated users"""
    redirect = 'https://testserver:80/accounts/login/?next=' + url
    response = client.get(url, **kwargs)
    nose.tools.eq_(response.status_code, 302)
    nose.tools.eq_(response['Location'], redirect)

def get_404(client, url):
    """Test a get on a url that is allowed with the users current credntials"""
    response = client.get(url, **kwargs)
    nose.tools.eq_(response.status_code, 404)

    return response


class TestFunctional(TestCase):
    """Functional tests for top level"""
    fixtures = ['holidays.json', 'jurisdictions.json', 'agency_types.json', 'test_agencies.json',
                'test_users.json', 'test_foiarequests.json', 'test_news.json']

    # tests for base level views
    def test_views(self):
        """Test views"""

        get_allowed(self.client, reverse('index'))
        get_allowed(self.client, '/sitemap.xml')
        get_allowed(self.client, '/search/')
