from rest_framework import serializers
from MiApp.models import Data

class DataSerializer(serializers.ModelSerializer):
	class Meta:
		model = Data
		fields = ['Identificador', 'OC', 'FechaApertura', 'Cantidad', 'PrecioLista', 'PrecioFacturado']