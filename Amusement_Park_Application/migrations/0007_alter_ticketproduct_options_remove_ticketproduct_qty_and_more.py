# Generated by Django 5.1.4 on 2025-01-03 12:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Amusement_Park_Application', '0006_alter_ticketproduct_options_remove_ticket_product_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ticketproduct',
            options={'verbose_name_plural': 'محصولات عودت وجه داده شده'},
        ),
        migrations.RemoveField(
            model_name='ticketproduct',
            name='qty',
        ),
        migrations.AddField(
            model_name='ticket',
            name='costumer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='ticket', to='Amusement_Park_Application.costumer', verbose_name='مشتری'),
        ),
        migrations.AddField(
            model_name='ticketproduct',
            name='quantity',
            field=models.PositiveIntegerField(default=1, verbose_name='تعداد'),
        ),
    ]
