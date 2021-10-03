# Generated by Django 3.2.7 on 2021-09-23 14:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0003_auto_20210923_1639'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membership',
            name='status',
            field=models.CharField(choices=[('PENDING_JOIN_REQUEST', 'Pending Join Request'), ('PENDING_INVITATION', 'Pending Invitation'), ('ACTIVE_MEMBERSHIP', 'Active Membership'), ('ADMIN', 'Admin')], default='ACTIVE_MEMBERSHIP', max_length=30),
        ),
    ]