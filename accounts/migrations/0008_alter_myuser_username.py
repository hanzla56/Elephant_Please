# Generated by Django 5.0.6 on 2024-07-15 12:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_alter_myuser_mobile_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myuser',
            name='username',
            field=models.CharField(max_length=200, unique=True),
        ),
    ]
