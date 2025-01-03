# Generated by Django 5.1.4 on 2025-01-03 10:33

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('Amusement_Park_Application', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='returnedsale',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='return_sale', to=settings.AUTH_USER_MODEL, verbose_name='فروشنده'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ticket', to='Amusement_Park_Application.product', verbose_name='محصول'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='ticket', to=settings.AUTH_USER_MODEL, verbose_name='فروشنده'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='ticket',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transaction_obj', to='Amusement_Park_Application.ticket', verbose_name='بلیت'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sale', to=settings.AUTH_USER_MODEL, verbose_name='فروشنده'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='transaction',
            field=models.ManyToManyField(related_name='tickets', to='Amusement_Park_Application.transaction', verbose_name='تراکنش ها'),
        ),
        migrations.CreateModel(
            name='ProductSaleReport',
            fields=[
            ],
            options={
                'verbose_name': 'گزارش فروش به تفکیک محصول',
                'verbose_name_plural': 'گزارش فروش به تفکیک محصول',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('Amusement_Park_Application.transaction',),
        ),
        migrations.CreateModel(
            name='Sale',
            fields=[
            ],
            options={
                'verbose_name': 'فروش',
                'verbose_name_plural': 'فروش',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('Amusement_Park_Application.transaction',),
        ),
    ]
