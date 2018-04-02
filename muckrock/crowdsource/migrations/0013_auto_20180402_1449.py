# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-04-02 18:49
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crowdsource', '0012_auto_20180306_1300'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='crowdsource',
            options={'verbose_name': 'assignment'},
        ),
        migrations.AlterModelOptions(
            name='crowdsourcechoice',
            options={'ordering': ('order',), 'verbose_name': 'assignment choice'},
        ),
        migrations.AlterModelOptions(
            name='crowdsourcedata',
            options={'verbose_name': 'assignment data'},
        ),
        migrations.AlterModelOptions(
            name='crowdsourcefield',
            options={'ordering': ('order',), 'verbose_name': 'assignment field'},
        ),
        migrations.AlterModelOptions(
            name='crowdsourceresponse',
            options={'verbose_name': 'assignment response'},
        ),
        migrations.AlterModelOptions(
            name='crowdsourcevalue',
            options={'verbose_name': 'assignment value'},
        ),
    ]
