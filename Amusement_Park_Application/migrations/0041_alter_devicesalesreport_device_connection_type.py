# Generated by Django 5.1.6 on 2025-06-16 16:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Amusement_Park_Application', '0040_devicesalesreport_device_connection_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='devicesalesreport',
            name='device_connection_type',
            field=models.CharField(choices=[('دستی', 'دستی'), ('IP', 'IP'), ('کابل سریال', 'کابل سریال'), ('هیچکدام', 'هیچکدام')], default='هیچکدام', max_length=55, verbose_name='نوع ارتباط با سیستم'),
        ),
    ]
