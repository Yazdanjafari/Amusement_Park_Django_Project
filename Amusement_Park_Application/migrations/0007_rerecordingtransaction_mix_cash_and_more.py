# Generated by Django 5.1.4 on 2025-01-27 13:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Amusement_Park_Application', '0006_transaction_mix_cash_transaction_mix_pc_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='rerecordingtransaction',
            name='mix_cash',
            field=models.PositiveBigIntegerField(blank=True, help_text='در صورتی که نوع فروش ترکیبی باشد این فیلد به صورت اتوماتیک دریافت میشود', null=True, verbose_name='مقدار قیمت پرداخت شده نقدی'),
        ),
        migrations.AddField(
            model_name='rerecordingtransaction',
            name='mix_pc',
            field=models.PositiveBigIntegerField(blank=True, help_text='در صورتی که نوع فروش ترکیبی باشد این فیلد به صورت اتوماتیک دریافت میشود', null=True, verbose_name='مقدار قیمت پرداخت شده با دستگاه کارتخوان'),
        ),
    ]
