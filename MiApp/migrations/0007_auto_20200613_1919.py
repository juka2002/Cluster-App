# Generated by Django 3.0.7 on 2020-06-14 00:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MiApp', '0006_auto_20200613_1904'),
    ]

    operations = [
        migrations.AlterField(
            model_name='data',
            name='Cantidad',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='data',
            name='FechaApertura',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='data',
            name='Identificador',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='data',
            name='PrecioFacturado',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True),
        ),
        migrations.AlterField(
            model_name='data',
            name='PrecioLista',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True),
        ),
    ]
