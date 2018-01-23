"""
URL mappings for the crowdsource app
"""

from django.conf.urls import url
from django.views.generic.base import RedirectView

from muckrock.crowdsource import views

urlpatterns = [
        url(r'^(?P<slug>[-\w]+)-(?P<idx>\d+)/$',
            views.CrowdsourceDetailView.as_view(),
            name='crowdsource-detail',
            ),
        url(r'^(?P<slug>[-\w]+)-(?P<idx>\d+)/draft/$',
            views.CrowdsourceUpdateView.as_view(),
            name='crowdsource-draft',
            ),
        url(r'^(?P<slug>[-\w]+)-(?P<idx>\d+)/form/$',
            views.CrowdsourceFormView.as_view(),
            name='crowdsource-assignment',
            ),
        url(r'^$',
            RedirectView.as_view(url='/assignment/list'),
            name='crowdsource-index',
            ),
        url(r'^list/$',
            views.CrowdsourceListView.as_view(),
            name='crowdsource-list',
            ),
        url(r'^create/$',
            views.CrowdsourceCreateView.as_view(),
            name='crowdsource-create',
            ),
        ]
