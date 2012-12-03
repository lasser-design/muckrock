"""
Tests using nose for the FOIA application
"""

from django.contrib.auth.models import User, AnonymousUser
from django.core.urlresolvers import reverse
from django.core import mail
from django.test import TestCase
import nose.tools

import datetime
import re
from operator import attrgetter

from foia.models import FOIARequest, FOIACommunication
from agency.models import Agency
from jurisdiction.models import Jurisdiction
from muckrock.tests import get_allowed, post_allowed, post_allowed_bad, get_post_unallowed, get_404

# allow methods that could be functions and too many public methods in tests
# pylint: disable=R0201
# pylint: disable=R0904

class TestFOIARequestUnit(TestCase):
    """Unit tests for FOIARequests"""
    fixtures = ['jurisdictions.json', 'agency_types.json', 'test_users.json', 'test_agencies.json',
                'test_profiles.json', 'test_foiarequests.json', 'test_foiacommunications.json']

    def setUp(self):
        """Set up tests"""
        # pylint: disable=C0103

        mail.outbox = []

        self.foia = FOIARequest.objects.get(pk=1)

    # models
    def test_foia_model_unicode(self):
        """Test FOIA Request model's __unicode__ method"""
        nose.tools.eq_(unicode(self.foia), 'Test 1')

    def test_foia_model_url(self):
        """Test FOIA Request model's get_absolute_url method"""

        nose.tools.eq_(self.foia.get_absolute_url(),
            reverse('foia-detail', kwargs={'idx': self.foia.pk, 'slug': 'test-1',
                                           'jurisdiction': 'massachusetts',
                                           'jidx': self.foia.jurisdiction.pk}))

    def test_foia_model_editable(self):
        """Test FOIA Request model's is_editable method"""

        foias = FOIARequest.objects.all().order_by('id')[:5]
        for foia in foias[:5]:
            if foia.status in ['started']:
                nose.tools.assert_true(foia.is_editable())
            else:
                nose.tools.assert_false(foia.is_editable())

    def test_foia_email(self):
        """Test FOIA sending an email to the user when a FOIA request is updated"""

        nose.tools.eq_(len(mail.outbox), 0)

        self.foia.status = 'submitted'
        self.foia.save()
        self.foia.submit()
        nose.tools.eq_(len(mail.outbox), 1)
        nose.tools.eq_(mail.outbox[0].to, ['requests@muckrock.com'])

        self.foia.status = 'processed'
        self.foia.save()
        self.foia.update()
        nose.tools.eq_(len(mail.outbox), 2)
        nose.tools.eq_(mail.outbox[1].to, [self.foia.user.email])

        # already updated, no additional email
        self.foia.status = 'fix'
        self.foia.save()
        self.foia.update()
        nose.tools.eq_(len(mail.outbox), 2)

        # if the user views it and clears the updated flag, we do get another email
        self.foia.updated = False
        self.foia.save()
        self.foia.status = 'rejected'
        self.foia.save()
        self.foia.update()
        nose.tools.eq_(len(mail.outbox), 3)

        foia = FOIARequest.objects.get(pk=6)
        foia.status = 'submitted'
        foia.save()
        foia.submit()
        nose.tools.eq_(mail.outbox[-1].from_email, '%s@requests.muckrock.com' % foia.get_mail_id())
        nose.tools.eq_(mail.outbox[-1].to, ['test@agency1.gov'])
        nose.tools.eq_(mail.outbox[-1].bcc,
                       ['other_a@agency1.gov', 'other_b@agency1.gov', 'requests@muckrock.com'])
        nose.tools.eq_(mail.outbox[-1].subject,
                       'Freedom of Information Request: %s' % foia.title)
        nose.tools.eq_(foia.status, 'processed')
        nose.tools.eq_(foia.date_submitted, datetime.date.today())
        nose.tools.ok_(foia.date_due > datetime.date.today())

    def test_foia_viewable(self):
        """Test all the viewable and embargo functions"""

        user1 = User.objects.get(pk=1)
        user2 = User.objects.get(pk=2)

        foias = list(FOIARequest.objects.filter(id__in=[1, 5, 11, 12, 13, 14]).order_by('id'))
        foias[1].date_embargo = datetime.date.today() + datetime.timedelta(10)
        foias[2].date_embargo = datetime.date.today() + datetime.timedelta(10)
        foias[3].date_embargo = datetime.date.today()
        foias[4].date_embargo = datetime.date.today() - datetime.timedelta(10)

        # check manager get_viewable against models is_viewable
        viewable_foias = FOIARequest.objects.get_viewable(user1)
        for foia in FOIARequest.objects.all():
            if foia in viewable_foias:
                nose.tools.assert_true(foia.is_viewable(user1))
            else:
                nose.tools.assert_false(foia.is_viewable(user1))

        viewable_foias = FOIARequest.objects.get_viewable(user2)
        for foia in FOIARequest.objects.all():
            if foia in viewable_foias:
                nose.tools.assert_true(foia.is_viewable(user2))
            else:
                nose.tools.assert_false(foia.is_viewable(user2))

        viewable_foias = FOIARequest.objects.get_public()
        for foia in FOIARequest.objects.all():
            if foia in viewable_foias:
                nose.tools.assert_true(foia.is_viewable(AnonymousUser()))
            else:
                nose.tools.assert_false(foia.is_viewable(AnonymousUser()))

        nose.tools.assert_true(foias[0].is_viewable(user1))
        nose.tools.assert_true(foias[1].is_viewable(user1))
        nose.tools.assert_true(foias[2].is_viewable(user1))
        nose.tools.assert_true(foias[3].is_viewable(user1))
        nose.tools.assert_true(foias[4].is_viewable(user1))

        nose.tools.assert_false(foias[0].is_viewable(user2))
        nose.tools.assert_true (foias[1].is_viewable(user2))
        nose.tools.assert_false(foias[2].is_viewable(user2))
        nose.tools.assert_true (foias[3].is_viewable(user2))
        nose.tools.assert_true (foias[4].is_viewable(user2))

        nose.tools.assert_false(foias[0].is_viewable(AnonymousUser()))
        nose.tools.assert_true (foias[1].is_viewable(AnonymousUser()))
        nose.tools.assert_false(foias[2].is_viewable(AnonymousUser()))
        nose.tools.assert_true (foias[3].is_viewable(AnonymousUser()))
        nose.tools.assert_true (foias[4].is_viewable(AnonymousUser()))

    def test_foia_set_mail_id(self):
        """Test the set_mail_id function"""
        foia = FOIARequest.objects.get(pk=17)
        foia.set_mail_id()
        mail_id = foia.mail_id
        nose.tools.ok_(re.match(r'\d{1,4}-\d{8}', mail_id))

        foia.set_mail_id()
        nose.tools.eq_(mail_id, foia.mail_id)


     # manager
    def test_manager_get_submitted(self):
        """Test the FOIA Manager's get_submitted method"""

        submitted_foias = FOIARequest.objects.get_submitted()
        for foia in FOIARequest.objects.all():
            if foia in submitted_foias:
                nose.tools.ok_(foia.status != 'started')
            else:
                nose.tools.ok_(foia.status == 'started')

    def test_manager_get_done(self):
        """Test the FOIA Manager's get_done method"""

        done_foias = FOIARequest.objects.get_done()
        for foia in FOIARequest.objects.all():
            if foia in done_foias:
                nose.tools.ok_(foia.status == 'done')
            else:
                nose.tools.ok_(
                        foia.status in ['started', 'submitted', 'processed',
                                        'fix', 'rejected', 'payment'])


class TestFOIAFunctional(TestCase):
    """Functional tests for FOIA"""
    fixtures = ['jurisdictions.json', 'agency_types.json', 'test_users.json', 'test_profiles.json',
                'test_foiarequests.json', 'test_foiacommunications.json', 'test_agencies.json']

    # views
    def test_foia_list(self):
        """Test the foia-list view"""

        response = get_allowed(self.client, reverse('foia-list'),
                ['foia/foiarequest_list.html', 'foia/base-single.html'], base='base-single.html')
        nose.tools.eq_(set(response.context['object_list']),
            set(FOIARequest.objects.get_viewable(AnonymousUser()).order_by('-date_submitted')[:10]))

    def test_foia_list_user(self):
        """Test the foia-list-user view"""

        for username in ['adam', 'bob']:
            response = get_allowed(self.client,
                                   reverse('foia-list-user', kwargs={'user_name': username}),
                                   ['foia/foiarequest_list.html', 'foia/base-single.html'],
                                   base='base-single.html')
            user = User.objects.get(username=username)
            nose.tools.eq_(set(response.context['object_list']),
                           set(FOIARequest.objects.get_viewable(AnonymousUser()).filter(user=user)))
            nose.tools.ok_(all(foia.user == user for foia in response.context['object_list']))

    def test_foia_sorted_list(self):
        """Test sorting on foia-list view"""

        for field, attr in [('title', 'title'), ('user', 'user.username'),
                            ('status', 'status'), ('jurisdiction', 'jurisdiction.name')]:
            for order in ['asc', 'desc']:

                response = get_allowed(self.client, reverse('foia-list') +
                                       '?field=%s&order=%s' % (field, order),
                                       ['foia/foiarequest_list.html', 'foia/base-single.html'],
                                       base='base-single.html')
                nose.tools.eq_([f.title for f in response.context['object_list']],
                               [f.title for f in sorted(response.context['object_list'],
                                                        key=attrgetter(attr),
                                                        reverse=order=='desc')])

    def test_foia_detail(self):
        """Test the foia-detail view"""

        foia = FOIARequest.objects.get(pk=2)
        get_allowed(self.client,
                    reverse('foia-detail', kwargs={'idx': foia.pk, 'slug': foia.slug,
                                                   'jurisdiction': foia.jurisdiction.slug,
                                                   'jidx': foia.jurisdiction.pk}),
                    ['foia/foiarequest_detail.html', 'foia/base.html'],
                    context = {'foia': foia})

    def test_feeds(self):
        """Test the RSS feed views"""

        get_allowed(self.client, reverse('foia-submitted-feed'))
        get_allowed(self.client, reverse('foia-done-feed'))

    def test_404_views(self):
        """Test views that should give a 404 error"""

        get_404(self.client, reverse('foia-list-user', kwargs={'user_name': 'test3'}))
        get_404(self.client, reverse('foia-detail', kwargs={'idx': 1, 'slug': 'test-c',
                                                       'jurisdiction': 'massachusetts',
                                                       'jidx': 1}))
        get_404(self.client, reverse('foia-detail', kwargs={'idx': 2, 'slug': 'test-c',
                                                       'jurisdiction': 'massachusetts',
                                                       'jidx': 1}))

    def test_unallowed_views(self):
        """Test private views while not logged in"""

        foia = FOIARequest.objects.get(pk=2)
        get_post_unallowed(self.client, reverse('foia-create'))
        get_post_unallowed(self.client, reverse('foia-update',
                                           kwargs={'jurisdiction': foia.jurisdiction.slug,
                                                   'jidx': foia.jurisdiction.pk,
                                                   'idx': foia.pk, 'slug': foia.slug}))

    def test_auth_views(self):
        """Test private views while logged in"""

        foia = FOIARequest.objects.get(pk=1)
        self.client.login(username='adam', password='abc')

        # get authenticated pages
        get_allowed(self.client, reverse('foia-create'),
                    ['foia/foiawizard_where.html', 'foia/base-submit.html'])

        get_allowed(self.client, reverse('foia-update',
                                    kwargs={'jurisdiction': foia.jurisdiction.slug,
                                            'jidx': foia.jurisdiction.pk,
                                            'idx': foia.pk, 'slug': foia.slug}),
                    ['foia/foiarequest_form.html', 'foia/base-submit.html'])

        get_404(self.client, reverse('foia-update',
                                kwargs={'jurisdiction': foia.jurisdiction.slug,
                                        'jidx': foia.jurisdiction.pk,
                                        'idx': foia.pk, 'slug': 'bad_slug'}))

        # post authenticated pages
        post_allowed_bad(self.client, reverse('foia-create'),
                         ['foia/foiawizard_where.html', 'foia/base-submit.html'])
        post_allowed_bad(self.client, reverse('foia-update',
                                         kwargs={'jurisdiction': foia.jurisdiction.slug,
                                                 'jidx': foia.jurisdiction.pk,
                                                 'idx': foia.pk, 'slug': foia.slug}),
                         ['foia/foiarequest_form.html', 'foia/base-submit.html'])

    def test_foia_submit_views(self):
        """Test submitting a FOIA request"""

        foia = FOIARequest.objects.get(pk=1)
        agency = Agency.objects.get(pk=3)
        self.client.login(username='adam', password='abc')

        # test for submitting a foia request for enough credits
        # tests for the wizard

        foia_data = {'title': 'test a', 'request': 'updated request', 'submit': 'Submit Request',
                     'agency': agency.pk, 'combo-name': agency.name}

        post_allowed(self.client,
                     reverse('foia-update',
                             kwargs={'jurisdiction': foia.jurisdiction.slug,
                                     'jidx': foia.jurisdiction.pk,
                                     'idx': foia.pk, 'slug': foia.slug}),
                     foia_data,
                     reverse('foia-detail', kwargs={'jurisdiction': 'massachusetts',
                                                    'jidx': foia.jurisdiction.pk,
                                                    'idx': foia.pk, 'slug': 'test-a'}))
        foia = FOIARequest.objects.get(title='test a')
        nose.tools.ok_(foia.first_request().startswith('updated request'))
        nose.tools.eq_(foia.status, 'submitted')

    def test_foia_save_views(self):
        """Test saving a FOIA request"""

        foia = FOIARequest.objects.get(pk=6)
        agency = Agency.objects.get(pk=2)
        self.client.login(username='bob', password='abc')

        foia_data = {'title': 'Test 6', 'request': 'saved request', 'submit': 'Save as Draft',
                     'agency': agency.pk, 'combo-name': agency.name}

        post_allowed(self.client,
                     reverse('foia-update',
                             kwargs={'jurisdiction': foia.jurisdiction.slug,
                                     'jidx': foia.jurisdiction.pk,
                                     'idx': foia.pk, 'slug': foia.slug}),
                     foia_data,
                     reverse('foia-detail', kwargs={'jurisdiction': foia.jurisdiction.slug,
                                                    'jidx': foia.jurisdiction.pk,
                                                    'idx': foia.pk, 'slug': foia.slug}))
        foia = FOIARequest.objects.get(title='Test 6')
        nose.tools.ok_(foia.first_request().startswith('saved request'))
        nose.tools.eq_(foia.status, 'started')
        nose.tools.eq_(foia.agency.pk, 2)

    def test_action_views(self):
        """Test action views"""

        foia = FOIARequest.objects.get(pk=1)
        self.client.login(username='adam', password='abc')

        get_allowed(self.client, reverse('foia-flag',
                                    kwargs={'jurisdiction': foia.jurisdiction.slug,
                                            'jidx': foia.jurisdiction.pk,
                                            'idx': foia.pk, 'slug': foia.slug}),
                    ['foia/foiarequest_action.html', 'foia/base-submit.html'])

        foia = FOIARequest.objects.get(pk=18)
        get_allowed(self.client, reverse('foia-pay',
                                    kwargs={'jurisdiction': foia.jurisdiction.slug,
                                            'jidx': foia.jurisdiction.pk,
                                            'idx': foia.pk, 'slug': foia.slug}),
                    ['registration/cc.html', 'registration/base.html'])

class TestFOIAIntegration(TestCase):
    """Integration tests for FOIA"""

    fixtures = ['jurisdictions.json', 'agency_types.json', 'test_users.json', 'test_agencies.json',
                'test_profiles.json', 'test_foiarequests.json', 'test_foiacommunications.json']

    def setUp(self):
        """Set up tests"""
        # pylint: disable=C0103
        # pylint: disable=E1003
        # pylint: disable=C0111

        mail.outbox = []

        import foia.models

        # Replace real date and time with mock ones so we can control today's/now's value
        # Unfortunately need to monkey patch this a lot of places, and it gets rather ugly
        class MockDate(datetime.date):
            def __add__(self, other):
                d = super(MockDate, self).__add__(other)
                return MockDate(d.year, d.month, d.day)
        class MockDateTime(datetime.datetime):
            def date(self):
                return MockDate(self.year, self.month, self.day)
        self.orig_date = datetime.date
        self.orig_datetime = datetime.datetime
        datetime.date = MockDate
        datetime.datetime = MockDateTime
        foia.models.date = datetime.date
        foia.models.datetime = datetime.datetime
        def save(self, *args, **kwargs):
            if self.date_followup:
                self.date_followup = MockDateTime(self.date_followup.year,
                                                  self.date_followup.month,
                                                  self.date_followup.day)
            if self.date_done:
                self.date_done = MockDateTime(self.date_done.year,
                                              self.date_done.month,
                                              self.date_done.day)
            super(FOIARequest, self).save(*args, **kwargs)
        self.FOIARequest_save = foia.models.FOIARequest.save
        foia.models.FOIARequest.save = save
        self.set_today(datetime.date(2010, 1, 1))

    def tearDown(self):
        """Tear down tests"""
        # pylint: disable=C0103

        import foia.models

        # restore the original date and datetime for other tests
        datetime.date = self.orig_date
        datetime.datetime = self.orig_datetime
        foia.models.date = datetime.date
        foia.models.datetime = datetime.datetime
        foia.models.FOIARequest.save = self.FOIARequest_save

    def set_today(self, date):
        """Set what datetime thinks today is"""
        datetime.date.today = classmethod(lambda cls: cls(date.year, date.month, date.day))
        datetime.datetime.now = classmethod(lambda cls: cls(date.year, date.month, date.day))

    def test_request_lifecycle_no_email(self):
        """Test a request going through the full cycle as if we had to physically mail it"""
        # pylint: disable=R0915
        # pylint: disable=W0212

        user = User.objects.get(username='adam')
        agency = Agency.objects.get(pk=3)
        jurisdiction = Jurisdiction.objects.get(pk=1)
        cal = jurisdiction.get_calendar()

        self.set_today(datetime.date(2010, 2, 1))
        nose.tools.eq_(len(mail.outbox), 0)

        ## create and submit request
        foia = FOIARequest.objects.create(
            user=user, title='Test with no email', slug='test-with-no-email',
            status='submitted', jurisdiction=jurisdiction, agency=agency)
        comm = FOIACommunication.objects.create(
            foia=foia, from_who='Muckrock', to_who='Test Agency', date=datetime.datetime.now(),
            response=False, communication='Test communication')
        foia.submit()

        # check that a notification has been sent to requests
        nose.tools.eq_(len(mail.outbox), 1)
        nose.tools.ok_(mail.outbox[-1].subject.startswith('[NEW]'))
        nose.tools.eq_(mail.outbox[-1].to, ['requests@muckrock.com'])

        ## two days pass, then the admin mails in the request
        self.set_today(datetime.date.today() + datetime.timedelta(2))
        foia.status = 'processed'
        foia.update_dates()
        foia.save()

        # make sure dates were set correctly
        nose.tools.eq_(foia.date_submitted, datetime.date(2010, 2, 3))
        nose.tools.eq_(foia.date_due, cal.business_days_from(datetime.date.today(),
                                                             jurisdiction.get_days()))
        nose.tools.eq_(foia.date_followup.date(),
                       max(foia.date_due, foia.last_comm().date.date() +
                                          datetime.timedelta(foia._followup_days())))
        nose.tools.ok_(foia.days_until_due is None)
        # no more mail should have been sent
        nose.tools.eq_(len(mail.outbox), 1)

        old_date_due = foia.date_due

        ## after 5 days agency replies with a fix needed
        self.set_today(datetime.date.today() + datetime.timedelta(5))
        comm = FOIACommunication.objects.create(
            foia=foia, from_who='Test Agency', to_who='Muckrock', date=datetime.datetime.now(),
            response=True, communication='Test communication')
        foia.status = 'fix'
        foia.save()
        foia.update(comm.anchor())

        # check that a notification has been sent to the user
        nose.tools.eq_(len(mail.outbox), 2)
        nose.tools.ok_(mail.outbox[-1].subject.startswith('[MuckRock]'))
        nose.tools.eq_(mail.outbox[-1].to, ['adam@example.com'])
        # make sure dates were set correctly
        nose.tools.eq_(foia.date_submitted, datetime.date(2010, 2, 3))
        nose.tools.ok_(foia.date_due is None)
        nose.tools.ok_(foia.date_followup is None)
        nose.tools.eq_(foia.days_until_due, cal.business_days_between(datetime.date(2010, 2, 8),
                                                                      old_date_due))

        old_days_until_due = foia.days_until_due

        ## after 10 days the user submits the fix and the admin submits it right away
        self.set_today(datetime.date.today() + datetime.timedelta(10))
        comm = FOIACommunication.objects.create(
            foia=foia, from_who='Muckrock', to_who='Test Agency', date=datetime.datetime.now(),
            response=False, communication='Test communication')
        foia.status = 'submitted'
        foia.save()
        foia.submit()

        # check that a notification has been sent to requests
        nose.tools.eq_(len(mail.outbox), 3)
        nose.tools.ok_(mail.outbox[-1].subject.startswith('[UPDATED]'))
        nose.tools.eq_(mail.outbox[-1].to, ['requests@muckrock.com'])

        foia.status = 'processed'

        foia.update_dates()
        foia.save()

        # make sure dates were set correctly
        nose.tools.eq_(foia.date_submitted, datetime.date(2010, 2, 3))
        nose.tools.eq_(foia.date_due, cal.business_days_from(datetime.date.today(),
                                                             old_days_until_due))
        nose.tools.eq_(foia.date_followup.date(),
                       max(foia.date_due, foia.last_comm().date.date() +
                                          datetime.timedelta(foia._followup_days())))
        nose.tools.ok_(foia.days_until_due is None)

        old_date_due = foia.date_due

        ## after 4 days agency replies with the documents
        self.set_today(datetime.date.today() + datetime.timedelta(4))
        comm = FOIACommunication.objects.create(
            foia=foia, from_who='Test Agency', to_who='Muckrock', date=datetime.date.today(),
            response=True, communication='Test communication')
        foia.status = 'done'
        foia.save()
        foia.update(comm.anchor())

        # check that a notification has not been sent to the user since they habe not
        # cleared the updated flag yet by viewing it
        nose.tools.eq_(len(mail.outbox), 3)
        # make sure dates were set correctly
        nose.tools.eq_(foia.date_submitted, datetime.date(2010, 2, 3))
        nose.tools.eq_(foia.date_due, old_date_due)
        nose.tools.ok_(foia.date_followup is None)
        nose.tools.ok_(foia.days_until_due is None)

