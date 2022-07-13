# Generated by Django 4.0.6 on 2022-07-13 09:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cart',
            name='id',
        ),
        migrations.AddField(
            model_name='cart',
            name='user_id',
            field=models.PositiveBigIntegerField(default=0, primary_key=True, serialize=False),
            preserve_default=False,
        ),
    ]
