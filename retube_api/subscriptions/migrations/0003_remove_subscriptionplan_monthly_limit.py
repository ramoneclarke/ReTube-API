# Generated by Django 4.1.7 on 2023-04-14 18:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0002_subscriptionplan_search_max_playlist_videos_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subscriptionplan',
            name='monthly_limit',
        ),
    ]