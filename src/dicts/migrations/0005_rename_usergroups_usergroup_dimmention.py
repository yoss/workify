# Generated by Django 4.2.13 on 2024-09-04 20:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('dicts', '0004_alter_usergroups_group'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='UserGroups',
            new_name='UserGroup',
        ),
        migrations.CreateModel(
            name='Dimmention',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='dicts.dimmention')),
            ],
            options={
                'verbose_name_plural': 'Dimmentions',
                'ordering': ['name'],
            },
        ),
    ]