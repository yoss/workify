# Generated by Django 4.2.13 on 2024-08-09 21:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('employees', '0003_alter_employee_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmployeeDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('sign_date', models.DateField()),
                ('document_file', models.FileField(upload_to='EmployeeDocuments/')),
                ('document_type', models.CharField(choices=[('contract', 'Contract'), ('amendment', 'Amendment'), ('termination', 'Termination Notice'), ('other', 'Other')], max_length=20)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='employees.employee')),
                ('reference_document', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='employees.employeedocument')),
            ],
        ),
    ]
