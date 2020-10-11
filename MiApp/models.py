from django.db import models

from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django.conf import settings

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
	if created:
		Token.objects.create(user=instance)


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
	GastoOT = models.FloatField(null=True, blank=True)
	Cliente = models.IntegerField(null=True, blank=True)
	PorCli = models.FloatField(null=True, blank=True)
	MontoOts = models.FloatField(null=True, blank=True)
	PorOts = models.FloatField(null=True, blank=True)
	Des = models.FloatField(null=True, blank=True)
	VIPx = models.FloatField(null=True, blank=True)
	VIP = models.FloatField(null=True, blank=True)
	Frecuencia = models.FloatField(null=True, blank=True)
	OtCli = models.FloatField(null=True, blank=True)
	Activo = models.IntegerField(null=True, blank=True)
	Alerta = models.IntegerField(null=True, blank=True)
	Desertor = models.IntegerField(null=True, blank=True)

	class Meta:
		verbose_name_plural = 'DataAnalysis'