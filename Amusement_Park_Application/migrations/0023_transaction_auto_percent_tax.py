# Generated by Django 5.1.6 on 2025-06-11 09:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Amusement_Park_Application', '0022_transaction_auto_percent_discount'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='auto_percent_tax',
            field=models.PositiveBigIntegerField(blank=True, null=True, verbose_name='درصد تخفیف'),
        ),
    ]
