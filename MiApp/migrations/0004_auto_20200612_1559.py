# Generated by Django 3.0.7 on 2020-06-12 20:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MiApp', '0003_auto_20200612_1406'),
    ]

    operations = [
        migrations.AlterField(
            model_name='data',
            name='PrecioFacturado',
            field=models.DecimalField(decimal_places=10, max_digits=20),
        ),
        migrations.AlterField(
            model_name='data',
            name='PrecioLista',
            field=models.DecimalField(decimal_places=10, max_digits=20),
        ),
    ]
