# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-24 20:35
from __future__ import unicode_literals

from django.db import migrations, models
from django.db.models import F, Case, When, DateTimeField


def populate_tracking_fields(apps, schema_editor):
    models = {}
    models['Phones'] = apps.get_model('hosting', 'Phone')._default_manager.all()
    models['Places'] = apps.get_model('hosting', 'Place')._default_manager.all()
    models['Profiles'] = apps.get_model('hosting', 'Profile')._default_manager.all()
    models['Websites'] = apps.get_model('hosting', 'Website')._default_manager.all()

    for name, objects in models.items():
        print(name)
        print('  deleted: ', objects.update(
            deleted_on=Case(
                When(deleted=False, then=None),
                default=F('modified'),
                output_field=DateTimeField())
        ))
        print('  checked: ', objects.update(
            checked_on=Case(
                When(checked=False, then=None),
                default=F('modified'),
                output_field=DateTimeField())
        ))


def unpopulate_tracking_fields(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('hosting', '0028_adding_validators'),
    ]

    operations = [
        migrations.AddField(
            model_name='phone',
            name='checked_on',
            field=models.DateTimeField(blank=True, default=None, null=True, verbose_name='checked on'),
        ),
        migrations.AddField(
            model_name='phone',
            name='deleted_on',
            field=models.DateTimeField(blank=True, default=None, null=True, verbose_name='delete on'),
        ),
        migrations.AddField(
            model_name='place',
            name='checked_on',
            field=models.DateTimeField(blank=True, default=None, null=True, verbose_name='checked on'),
        ),
        migrations.AddField(
            model_name='place',
            name='deleted_on',
            field=models.DateTimeField(blank=True, default=None, null=True, verbose_name='delete on'),
        ),
        migrations.AddField(
            model_name='profile',
            name='checked_on',
            field=models.DateTimeField(blank=True, default=None, null=True, verbose_name='checked on'),
        ),
        migrations.AddField(
            model_name='profile',
            name='deleted_on',
            field=models.DateTimeField(blank=True, default=None, null=True, verbose_name='delete on'),
        ),
        migrations.AddField(
            model_name='website',
            name='checked_on',
            field=models.DateTimeField(blank=True, default=None, null=True, verbose_name='checked on'),
        ),
        migrations.AddField(
            model_name='website',
            name='deleted_on',
            field=models.DateTimeField(blank=True, default=None, null=True, verbose_name='delete on'),
        ),

        migrations.RunPython(populate_tracking_fields, reverse_code=unpopulate_tracking_fields),
    ]
