# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2017-01-24 20:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foia', '0020_auto_20170119_2227'),
    ]

    operations = [
        migrations.AlterField(
            model_name='communicationerror',
            name='reason',
            field=models.CharField(max_length=255),
        ),
    ]
