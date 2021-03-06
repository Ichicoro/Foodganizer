# Generated by Django 3.2.7 on 2021-10-03 14:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0004_alter_membership_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membership',
            name='status',
            field=models.CharField(choices=[('PENDING_JOIN_REQUEST', 'Pending Join Request'), ('PENDING_INVITATION', 'Pending Invitation'), ('ACTIVE_MEMBERSHIP', 'Active Membership'), ('ADMIN', 'Admin')], max_length=30),
        ),
    ]
