from rest_framework import serializers
from MiApp.models import Data, DataAnalysis
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

class DataSerializer(serializers.ModelSerializer):
	class Meta:
		model = Data
		#si quiero especificar que se muestra en la api
		#fields = ['id', 'Identificador', 'OC', 'FechaApertura', 'Cantidad', 'PrecioLista', 'PrecioFacturado']
		fields = '__all__'

class DataAnalysisSerializer(serializers.ModelSerializer):
	class Meta:
		model = DataAnalysis
		#si quiero especificar que se muestra en la api
		#fields = ['id', 'Identificador', 'OC', 'FechaApertura', 'Cantidad', 'PrecioLista', 'PrecioFacturado']
		fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		fields = ('id','username', 'email','password')
		extra_kwargs = {'password':{'write_only':True,'required':True}}

	def create(self, validated_data):
		user = User.objects.create_user(**validated_data)
		print(user)
		Token.objects.create(user=user)
		return user