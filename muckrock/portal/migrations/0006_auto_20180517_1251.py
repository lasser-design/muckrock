# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-05-17 16:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0005_auto_20171129_1549'),
    ]

    operations = [
        migrations.AlterField(
            model_name='portal',
            name='type',
            field=models.CharField(choices=[(b'foiaonline', b'FOIAonline'), (b'govqa', b'GovQA'), (b'nextrequest', b'NextRequest'), (b'foiaxpress', b'FOIAXpress'), (b'fbi', b'FBI eFOIPA Portal'), (b'webform', b'Web Form'), (b'other', b'Other')], max_length=11),
        ),
    ]
