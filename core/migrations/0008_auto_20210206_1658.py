# Generated by Django 3.1.5 on 2021-02-06 16:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_presentation_presented_remotely'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='presentation',
            name='year',
        ),
        migrations.AddField(
            model_name='presentation',
            name='date',
            field=models.DateField(default='2020-01-01'),
            preserve_default=False,
        ),
    ]
