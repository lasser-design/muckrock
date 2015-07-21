"""
Serilizers for the Agency application API
"""

from rest_framework import serializers

from muckrock.agency.models import Agency, AgencyType

# pylint: disable=too-few-public-methods

class AgencySerializer(serializers.ModelSerializer):
    """Serializer for Agency model"""
    types = serializers.RelatedField(
        many=True, queryset=AgencyType.objects.all())

    def __init__(self, *args, **kwargs):
        # pylint: disable=no-member
        # pylint: disable=super-on-old-class
        super(AgencySerializer, self).__init__(*args, **kwargs)

        if 'request' not in self.context:
            self.fields.pop('email')
            self.fields.pop('other_emails')
            return

        request = self.context['request']

        if not request.user.is_staff:
            self.fields.pop('email')
            self.fields.pop('other_emails')

    class Meta:
        model = Agency
        fields = ('id', 'name', 'slug', 'jurisdiction', 'types', 'public_notes', 'address',
                  'contact_salutation', 'contact_first_name', 'contact_last_name',
                  'contact_title', 'url', 'expires', 'phone', 'fax', 'approved', 'appeal_agency',
                  'can_email_appeals', 'image_attr_line', 'stale', 'website', 'twitter',
                  'twitter_handles', 'foia_logs', 'foia_guide', 'exempt', 'email', 'other_emails',
                  'parent')

