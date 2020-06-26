from rest_framework import serializers
from MiApp.models import Data #DataAnalysis

class DataSerializer(serializers.ModelSerializer):
	class Meta:
		model = Data
		#si quiero especificar que se muestra en la api
		#fields = ['id', 'Identificador', 'OC', 'FechaApertura', 'Cantidad', 'PrecioLista', 'PrecioFacturado']
		fields = '__all__'

# class DataAnalysisSerializer(serializers.ModelSerializer):
# 	class Meta:
# 		model = DataAnalysis
# 		#si quiero especificar que se muestra en la api
# 		#fields = ['id', 'Identificador', 'OC', 'FechaApertura', 'Cantidad', 'PrecioLista', 'PrecioFacturado']
# 		fields = '__all__'