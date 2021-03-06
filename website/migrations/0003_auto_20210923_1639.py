# Generated by Django 3.2.7 on 2021-09-23 14:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0002_postit_last_edited_by'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='membership',
            name='is_admin',
        ),
        migrations.AlterField(
            model_name='membership',
            name='status',
            field=models.CharField(choices=[('PJR', 'Pending Join Request'), ('PI', 'Pending Invitation'), ('AM', 'Active Membership'), ('AMA', 'Active Membership Admin')], default='AM', max_length=3),
        ),
    ]
