# Generated by Django 4.2.1 on 2023-10-14 12:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0010_project_metadata_added'),
    ]

    operations = [
        migrations.CreateModel(
            name='Lock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('row_key', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'db_table': 'lock',
            },
        ),
    ]
