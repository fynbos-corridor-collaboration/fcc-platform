# Generated by Django 3.2.8 on 2023-02-02 12:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0057_auto_20230202_1045'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gardenmanager',
            name='token',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]