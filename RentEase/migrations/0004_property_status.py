# Generated by Django 5.1.3 on 2024-11-22 23:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('RentEase', '0003_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='property',
            name='status',
            field=models.CharField(choices=[('available', 'Available'), ('booked', 'Booked'), ('unavailable', 'Unavailable')], default='available', max_length=20),
        ),
    ]