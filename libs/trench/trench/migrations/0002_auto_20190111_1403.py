# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-01-11 14:03
from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("trench", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="mfamethod",
            old_name="backup_codes",
            new_name="_backup_codes",
        ),
        migrations.AlterField(
            model_name="mfamethod",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="mfa_methods",
                to=settings.AUTH_USER_MODEL,
                verbose_name="user",
            ),
        ),
    ]
