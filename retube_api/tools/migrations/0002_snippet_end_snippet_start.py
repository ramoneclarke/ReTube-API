# Generated by Django 4.1.7 on 2023-03-12 19:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='snippet',
            name='end',
            field=models.CharField(default='00:00:02.00', max_length=40),
        ),
        migrations.AddField(
            model_name='snippet',
            name='start',
            field=models.CharField(default='00:00:01.00', max_length=40),
        ),
    ]
