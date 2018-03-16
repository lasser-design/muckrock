# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-02-13 15:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jurisdiction', '0015_auto_20180213_1346'),
    ]

    operations = [
        migrations.AddField(
            model_name='law',
            name='fee_schedule',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='law',
            name='trade_secrets',
            field=models.BooleanField(default=False, help_text=b'Can trade secrets be made public?'),
        ),
    ]
