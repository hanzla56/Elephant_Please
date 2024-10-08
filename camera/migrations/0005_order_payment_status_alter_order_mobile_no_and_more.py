# Generated by Django 5.0.6 on 2024-07-11 13:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('camera', '0004_item_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_status',
            field=models.CharField(choices=[('p', 'pending'), ('s', 'successful')], default='p', max_length=1),
        ),
        migrations.AlterField(
            model_name='order',
            name='mobile_no',
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name='order',
            name='quantity',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
