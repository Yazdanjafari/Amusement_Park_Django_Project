# Generated by Django 5.1.4 on 2025-01-07 11:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Amusement_Park_Application', '0006_alter_transaction_manual_discount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='returnedtransaction',
            name='desc',
            field=models.TextField(blank=True, null=True, verbose_name='توضیحات'),
        ),
    ]