# Generated by Django 4.2.13 on 2024-08-17 21:19

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('logo', models.ImageField(blank=True, upload_to='ClientLogo/')),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
    ]
