from django.db import models

# Create your models here.
class Data(models.Model):
	Identificador = models.CharField(max_length=500)
	OC = models.CharField(max_length=500, null=True, blank=True)
	FechaApertura = models.DateTimeField()
	Cantidad = models.IntegerField()
	PrecioLista = models.DecimalField(max_digits=20, decimal_places=2)
	PrecioFacturado = models.DecimalField(max_digits=20, decimal_places=2)

	class Meta:
		verbose_name_plural = 'Data'

