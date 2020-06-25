from django.db import models

# Create your models here.
class Data(models.Model):
	id = models.AutoField(primary_key=True)
	Identificador = models.CharField(max_length=500, null=True, blank=True)
	OC = models.CharField(max_length=500, null=True, blank=True)
	FechaApertura = models.DateTimeField(null=True, blank=True)
	Cantidad = models.IntegerField(null=True, blank=True)
	PrecioLista = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
	PrecioFacturado = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

	class Meta:
		verbose_name_plural = 'Data'

class DataAnalysis(models.Model):
	id = models.AutoField(primary_key=True)
	Segment = models.CharField(max_length=500, null=True, blank=True)
	GastoOT = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
	Cliente = models.IntegerField(null=True, blank=True)
	PorCliente = models.FloatField(null=True, blank=True)
	MontoOts = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
	PorMontoOts = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
	Descuento = models.FloatField(null=True, blank=True)
	VIPx = models.FloatField(null=True, blank=True)
	VIP = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
	Frecuencia = models.FloatField(null=True, blank=True)
	OtCliente = models.FloatField(null=True, blank=True)
	Activo = models.IntegerField(null=True, blank=True)
	Alerta = models.IntegerField(null=True, blank=True)
	Desertor = models.IntegerField(null=True, blank=True)

	class Meta:
		verbose_name_plural = 'DataAnalysis'