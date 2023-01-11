# Generated by Django 3.2.9 on 2023-01-11 20:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0030_merge_20210427_1152'),
        ('jurisdiction', '0025_alter_invokedexemption_properly_invoked'),
    ]

    operations = [
        migrations.AddField(
            model_name='jurisdiction',
            name='appeal_agency',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='appeal_jurisdictions', to='agency.agency'),
        ),
    ]
