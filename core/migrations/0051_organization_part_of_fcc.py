# Generated by Django 3.2.5 on 2021-10-26 01:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0050_organization_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='part_of_fcc',
            field=models.BooleanField(db_index=True, default=True),
        ),
    ]