# Generated by Django 4.2.13 on 2024-09-20 12:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dicts', '0008_employeedocumenttypes'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='employeedocumenttypes',
            options={'ordering': ['code'], 'verbose_name_plural': 'Employee Document Types'},
        ),
        migrations.AlterField(
            model_name='employeedocumenttypes',
            name='code',
            field=models.CharField(max_length=25, unique=True),
        ),
    ]