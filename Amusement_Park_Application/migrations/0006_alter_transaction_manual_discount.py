# Generated by Django 5.1.4 on 2025-01-05 16:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Amusement_Park_Application', '0005_alter_transaction_manual_discount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaction',
            name='manual_discount',
            field=models.PositiveIntegerField(blank=True, default=0, null=True, verbose_name='تخفیف دستی'),
        ),
    ]