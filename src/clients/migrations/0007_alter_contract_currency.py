# Generated by Django 4.2.13 on 2024-08-31 21:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dicts', '0003_usergroups'),
        ('clients', '0006_alter_contract_currency'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contract',
            name='currency',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='dicts.currency'),
        ),
    ]
