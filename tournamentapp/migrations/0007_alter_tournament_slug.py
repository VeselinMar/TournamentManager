# Generated by Django 5.2.4 on 2025-07-18 17:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournamentapp', '0006_remove_tournament_public_id_tournament_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tournament',
            name='slug',
            field=models.SlugField(blank=True, max_length=255, unique=True),
        ),
    ]
