# Generated by Django 4.0.1 on 2022-01-31 16:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0005_alter_membership_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='storeditem',
            name='expiry_date',
            field=models.DateField(blank=True, default=None, null=True),
        ),
    ]
