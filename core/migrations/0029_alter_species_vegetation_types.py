# Generated by Django 3.2 on 2021-05-28 15:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_auto_20210528_1511'),
    ]

    operations = [
        migrations.AlterField(
            model_name='species',
            name='vegetation_types',
            field=models.ManyToManyField(blank=True, related_name='species', to='core.VegetationType'),
        ),
    ]