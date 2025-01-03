# Generated by Django 5.1.4 on 2025-01-03 16:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Amusement_Park_Application', '0017_delete_productsalereport'),
    ]

    operations = [
        migrations.CreateModel(
            name='SalesSummaryByCustomer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('customer_name', models.CharField(max_length=255, verbose_name='نام مشتری')),
                ('total_quantity_purchased', models.PositiveIntegerField(verbose_name='مجموع تعداد بلیط های خریداری کرده')),
                ('total_sales_amount', models.PositiveIntegerField(verbose_name='مجموع قیمت های خریداری شده توسط این مشتری')),
            ],
            options={
                'verbose_name': 'خلاصه فروش بر اساس مشتری',
                'verbose_name_plural': 'خلاصه فروش بر اساس مشتریان',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='SalesSummaryByProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_name', models.CharField(max_length=255, verbose_name='نام محصول')),
                ('unit_price', models.PositiveIntegerField(verbose_name='قیمت واحد محصول')),
                ('total_quantity_sold', models.PositiveIntegerField(verbose_name='مجموع تعداد بلیط های فروخته شده')),
                ('total_sales_amount', models.PositiveIntegerField(verbose_name='مجموع قیمت های فروش')),
            ],
            options={
                'verbose_name': 'خلاصه فروش بر اساس محصول',
                'verbose_name_plural': 'خلاصه فروش بر اساس محصولات',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='SalesSummaryByUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_name', models.CharField(max_length=255, verbose_name='نام فروشنده')),
                ('total_quantity_sold', models.PositiveIntegerField(verbose_name='مجموع تعداد بلیط های فروخته شده توسط این فروشنده')),
                ('total_sales_amount', models.PositiveIntegerField(verbose_name='مجموع قیمت های فروش توسط این فروشنده')),
            ],
            options={
                'verbose_name': 'خلاصه فروش بر اساس فروشنده',
                'verbose_name_plural': 'خلاصه فروش بر اساس فروشندگان',
                'managed': False,
            },
        ),
    ]
