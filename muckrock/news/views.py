"""
Views for the news application
"""

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Prefetch, Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView
from django.views.generic.dates import (
    DateDetailView,
    DayArchiveView,
    MonthArchiveView,
    YearArchiveView,
)

# MuckRock
from muckrock.core.utils import cache_get_or_set
from muckrock.core.views import MRSearchFilterListView, PaginationMixin
from muckrock.news.filters import (
    ArticleAuthorFilterSet,
    ArticleDateRangeFilterSet,
)
from muckrock.news.models import Article
from muckrock.project.forms import ProjectManagerForm
from muckrock.project.models import Project
from muckrock.tags.models import Tag, parse_tags


class NewsDetail(DateDetailView):
    """View for news detail"""
    template_name = 'news/detail.html'
    date_field = 'pub_date'

    def get_queryset(self):
        """Get articles for this view"""
        queryset = Article.objects.prefetch_authors().prefetch_editors()
        if self.request.user.is_staff:
            return queryset.all()
        else:
            return queryset.get_published()

    def get_allow_future(self):
        """Can future posts be seen?"""
        return self.request.user.is_staff

    def get_related_articles(self, article):
        """Get articles related to the current one."""
        # articles in the same project as this one
        project_filter = Q(projects__in=article.projects.all())
        # articles with the same tag as this one
        tag_filter = Q(tags__in=article.tags.all())
        # articles in projects with the same tag as this one
        project_tag_filter = Q(projects__tags__in=article.tags.all())
        related_articles = (
            Article.objects.get_published()
            .filter(project_filter | tag_filter | project_tag_filter)
            .exclude(pk=article.pk).distinct().prefetch_authors()
            .prefetch_editors()
        )
        return related_articles[:4]

    def get_context_data(self, **kwargs):
        context = super(NewsDetail, self).get_context_data(**kwargs)
        context['projects'] = context['object'].projects.all()
        context['foias'] = (
            context['object'].foias.get_public().select_related_view()
            .get_public_file_count()
        )
        context['related_articles'] = self.get_related_articles(
            context['object']
        )
        context['sidebar_admin_url'] = reverse(
            'admin:news_article_change', args=(context['object'].pk,)
        )
        context['stripe_pk'] = settings.STRIPE_PUB_KEY
        return context

    def post(self, request, **kwargs):
        """Handles POST requests on article pages"""
        # pylint:disable=unused-argument
        article = self.get_object()
        authorized = self.request.user.is_staff
        action = request.POST.get('action')
        if not authorized:
            return HttpResponseForbidden()
        if action == 'projects':
            form = ProjectManagerForm(request.POST, user=request.user)
            if form.is_valid():
                projects = form.cleaned_data['projects']
                article.projects = projects
        tags = request.POST.get('tags')
        if tags:
            tag_set = set()
            for tag in parse_tags(tags):
                new_tag, _ = Tag.objects.get_or_create(name=tag)
                tag_set.add(new_tag)
            article.tags.set(*tag_set)
        return redirect(article)


class NewsExploreView(TemplateView):
    """Shows the most interesting and worthwhile articles."""
    template_name = 'news/explore.html'

    def get_context_data(self, **kwargs):
        """Adds interesting articles to the explore page."""
        context = super(NewsExploreView, self).get_context_data(**kwargs)
        recent_articles = cache_get_or_set(
            'hp:articles', lambda: (
                Article.objects.get_published().prefetch_related(
                    'authors',
                    'authors__profile',
                    'projects',
                )[:5]
            ), 600
        )
        context['featured_projects'] = (
            Project.objects.get_visible(
                self.request.user
            ).filter(featured=True).prefetch_related(
                Prefetch(
                    'articles__authors',
                    queryset=User.objects.select_related('profile')
                )
            ).optimize()
        )
        context['recent_articles'] = recent_articles
        context['top_tags'] = Article.tags.most_common()[:15]
        return context


class NewsYear(PaginationMixin, YearArchiveView):
    """View for year archive"""
    date_field = 'pub_date'
    make_object_list = True
    queryset = Article.objects.get_published().prefetch_authors()
    template_name = 'news/archives/year_archive.html'


class NewsMonth(PaginationMixin, MonthArchiveView):
    """View for month archive"""
    date_field = 'pub_date'
    make_object_list = True
    queryset = Article.objects.get_published().prefetch_authors()
    template_name = 'news/archives/month_archive.html'


class NewsDay(PaginationMixin, DayArchiveView):
    """View for day archive"""
    date_field = 'pub_date'
    make_object_list = True
    queryset = Article.objects.get_published().prefetch_authors()
    template_name = 'news/archives/day_archive.html'


class NewsListView(MRSearchFilterListView):
    """List of news articles"""
    model = Article
    title = 'News'
    filter_class = ArticleDateRangeFilterSet
    template_name = 'news/list.html'
    default_sort = 'pub_date'
    default_order = 'desc'
    queryset = Article.objects.get_published().prefetch_authors()
    paginate_by = 10
    sort_map = {}

    def get_context_data(self, **kwargs):
        """Add a list of all the years we've published to the context."""
        context = super(NewsListView, self).get_context_data(**kwargs)
        articles_by_date = self.queryset.order_by('pub_date')
        if not articles_by_date.exists():
            raise Http404
        years = range(
            articles_by_date.first().pub_date.year,
            articles_by_date.last().pub_date.year +
            1,  # the range function stops at n - 1
        )
        years.reverse()
        context['years'] = years
        return context
