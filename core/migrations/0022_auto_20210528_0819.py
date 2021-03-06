# Generated by Django 3.2 on 2021-05-28 08:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_vegetationtype_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vegetationtype',
            name='cape_town_cover',
            field=models.FloatField(help_text='In %'),
        ),
        migrations.AlterField(
            model_name='vegetationtype',
            name='current_cape_town_area',
            field=models.FloatField(help_text='In km2'),
        ),
    ]
