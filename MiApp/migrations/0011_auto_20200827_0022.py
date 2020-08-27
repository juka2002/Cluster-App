# Generated by Django 3.0.7 on 2020-08-27 00:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MiApp', '0010_auto_20200827_0013'),
    ]

    operations = [
        migrations.RenameField(
            model_name='dataanalysis',
            old_name='Descuento',
            new_name='Des',
        ),
        migrations.RenameField(
            model_name='dataanalysis',
            old_name='PorCliente',
            new_name='PorCli',
        ),
        migrations.RenameField(
            model_name='dataanalysis',
            old_name='PorMontoOts',
            new_name='PorOts',
        ),
        migrations.RemoveField(
            model_name='dataanalysis',
            name='OtCliente',
        ),
        migrations.AddField(
            model_name='dataanalysis',
            name='OtCli',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
