# Generated by Django 3.2 on 2021-05-28 09:16

from django.db import migrations, models
import stdimage.models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_auto_20210528_0819'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='format',
            field=models.CharField(choices=[('HTML', 'HTML'), ('MARK', 'Markdown'), ('MARK_HTML', 'Markdown and HTML')], default='none', max_length=9),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='page',
            name='image',
            field=stdimage.models.StdImageField(blank=True, null=True, upload_to='pages'),
        ),
    ]
