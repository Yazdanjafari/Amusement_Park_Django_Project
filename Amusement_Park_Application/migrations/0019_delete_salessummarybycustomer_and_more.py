# Generated by Django 5.1.4 on 2025-01-03 17:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Amusement_Park_Application', '0018_salessummarybycustomer_salessummarybyproduct_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='SalesSummaryByCustomer',
        ),
        migrations.DeleteModel(
            name='SalesSummaryByProduct',
        ),
        migrations.DeleteModel(
            name='SalesSummaryByUser',
        ),
    ]