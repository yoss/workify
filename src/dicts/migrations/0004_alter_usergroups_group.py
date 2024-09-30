# Generated by Django 4.2.13 on 2024-08-31 21:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('dicts', '0003_usergroups'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usergroups',
            name='group',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='auth.group'),
        ),
    ]
