# Generated by Django 5.1.4 on 2025-01-04 16:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Amusement_Park_Application', '0032_alter_successfultransactionlog_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='successfultransactionlog',
            name='kind',
            field=models.CharField(choices=[('فروش', 'فروش'), ('فروش مجدد', 'فروش مجدد'), ('عودت وجه', 'عودت وجه')], max_length=30, verbose_name='نوع تراکنش'),
        ),
    ]