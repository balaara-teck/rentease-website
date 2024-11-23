# Generated by Django 5.1.3 on 2024-11-23 01:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('RentEase', '0004_property_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddField(
            model_name='property',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
    ]