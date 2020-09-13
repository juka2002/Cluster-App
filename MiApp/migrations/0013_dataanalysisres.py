# Generated by Django 3.0.7 on 2020-08-30 12:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MiApp', '0012_auto_20200827_0045'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataAnalysisRes',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('Segment', models.CharField(blank=True, max_length=500, null=True)),
                ('GastoOT', models.FloatField(blank=True, null=True)),
                ('Cliente', models.IntegerField(blank=True, null=True)),
                ('PorCli', models.FloatField(blank=True, null=True)),
                ('MontoOts', models.FloatField(blank=True, null=True)),
                ('PorOts', models.FloatField(blank=True, null=True)),
                ('Des', models.FloatField(blank=True, null=True)),
                ('VIPx', models.FloatField(blank=True, null=True)),
                ('VIP', models.FloatField(blank=True, null=True)),
                ('Frecuencia', models.FloatField(blank=True, null=True)),
                ('OtCli', models.FloatField(blank=True, null=True)),
                ('Activo', models.IntegerField(blank=True, null=True)),
                ('Alerta', models.IntegerField(blank=True, null=True)),
                ('Desertor', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'verbose_name_plural': 'DataAnalysisRes',
            },
        ),
    ]