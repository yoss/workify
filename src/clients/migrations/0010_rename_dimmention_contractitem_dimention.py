# Generated by Django 4.2.13 on 2024-09-05 22:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0009_contractitem_dimmention'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contractitem',
            old_name='dimmention',
            new_name='dimention',
        ),
    ]
