# Generated by Django 3.2 on 2021-05-28 08:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_photo_author'),
    ]

    operations = [
        migrations.AlterField(
            model_name='photo',
            name='position',
            field=models.PositiveSmallIntegerField(db_index=True, default=1),
        ),
        migrations.AlterField(
            model_name='species',
            name='family',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='species', to='core.family'),
        ),
        migrations.AlterField(
            model_name='species',
            name='genus',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='species', to='core.genus'),
        ),
        migrations.CreateModel(
            name='VegetationType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('historical_cover', models.PositiveSmallIntegerField(help_text='Cover in km2')),
                ('cape_town_cover', models.DecimalField(decimal_places=1, help_text='In %', max_digits=3)),
                ('current_cape_town_area', models.DecimalField(decimal_places=1, help_text='In km2', max_digits=4)),
                ('conserved_cape_town', models.PositiveSmallIntegerField(help_text='Conserved or managed, in km2')),
                ('redlist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.redlist')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
    ]