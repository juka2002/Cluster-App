from django.db import models

# Create your models here.
class Data(models.Model):
	Identificador = models.CharField(max_length=500)
	OC = models.CharField(max_length=500)
	FechaApertura = models.DateTimeField()
	Cantidad = models.IntegerField()
	PrecioLista = models.IntegerField()
	PrecioFacturado = models.IntegerField()

	class Meta:
		verbose_name_plural = 'Data'