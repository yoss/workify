# Generated by Django 4.2.13 on 2024-09-20 12:47

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0008_alter_employeerate_currency'),
    ]

    operations = [
        migrations.AddField(
            model_name='employeerate',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='employeerate',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_created', to='employees.employee'),
        ),
        migrations.AddField(
            model_name='employeerate',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='employeerate',
            name='updated_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_updated', to='employees.employee'),
        ),
    ]
