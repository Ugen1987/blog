# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-09-02 10:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_userphone'),
        ('accounts', '0003_auto_20180812_1423'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='phone',
            field=models.ManyToManyField(blank=True, null=True, to='posts.UserPhone'),
        ),
    ]
