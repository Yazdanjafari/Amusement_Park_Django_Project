# Generated by Django 5.1.6 on 2025-06-15 11:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('Amusement_Park_Application', '0035_alter_salesreport_created_at_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='salesreport',
            old_name='created_at',
            new_name='create_at',
        ),
        migrations.RenameField(
            model_name='salesreport',
            old_name='updated_at',
            new_name='update_at',
        ),
    ]
