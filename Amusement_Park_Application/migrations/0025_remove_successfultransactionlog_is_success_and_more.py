# Generated by Django 5.1.4 on 2025-01-04 14:40

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Amusement_Park_Application', '0024_successfultransactionlog'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='successfultransactionlog',
            name='is_success',
        ),
        migrations.RemoveField(
            model_name='successfultransactionlog',
            name='transaction_id',
        ),
        migrations.AddField(
            model_name='successfultransactionlog',
            name='desc',
            field=models.TextField(blank=True, null=True, verbose_name='توضیحات'),
        ),
        migrations.AddField(
            model_name='successfultransactionlog',
            name='type',
            field=models.CharField(choices=[('pc', 'pc pos'), ('cash', 'نقدی'), ('card', 'کارتی')], default='pc', max_length=10, verbose_name='نوع پرداخت'),
        ),
        migrations.AddField(
            model_name='successfultransactionlog',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, related_name='successful_sales', to=settings.AUTH_USER_MODEL, verbose_name='فروشنده'),
            preserve_default=False,
        ),
    ]