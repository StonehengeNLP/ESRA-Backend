# Generated by Django 2.2.5 on 2020-12-30 11:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('esra_backend', '0004_auto_20201230_0041'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paperauthoraffiliation',
            name='affiliation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='esra_backend.Affiliation'),
        ),
    ]