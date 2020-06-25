from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from api.serializers import DataSerializer, DataAnalysisSerializer
from MiApp.models import Data, DataAnalysis
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework import mixins
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
import numpy as np

# Create your views here.
#Hago la api con el data ViewSet
class DataViewSet(viewsets.ModelViewSet):
	serializer_class = DataSerializer
	queryset = Data.objects.all()
	# authentication_classes = [SessionAuthentication, BasicAuthentication]
	# permission_classes = [IsAuthenticated]

class DataAnalysisSet(viewsets.ModelViewSet):
	serializer_class = DataAnalysisSerializer
	queryset = DataAnalysis.objects.all()
	# authentication_classes = [SessionAuthentication, BasicAuthentication]
	# permission_classes = [IsAuthenticated]

@api_view(['POST'])
def read_data(request):
	try:


		return Response("ok")
	except ValueError as e:
		return Response(e.args[0], status.HTTP_400_BAD_REQUEST)

#Aquí hago la api creada en forma Genérica
# class GenericAPIView(
# 	generics.GenericAPIView,
# 	mixins.ListModelMixin,
# 	mixins.CreateModelMixin,
# 	mixins.UpdateModelMixin,
# 	mixins.RetrieveModelMixin,
# 	mixins.DestroyModelMixin,
# 	):
# 	serializer_class = DataSerializer
# 	queryset = Data.objects.all()
# 	lookup_field = 'id'
# 	#quitar el BasicAuthentication en producción
# 	authentication_classes = [SessionAuthentication, BasicAuthentication]
# 	permission_classes = [IsAuthenticated]
#
# 	def get(self, request, id = None):
#
# 		if id:
# 			return self.retrieve(request)
#
# 		else:
# 			return self.list(request)
#
# 		return self.list(request)
#
# 	def post(self, request):
# 		return self.create(request)
#
# 	def put(self, request, id=None):
# 		return self.update(request, id)
#
# 	def delete(self, request, id):
# 		return self.destroy(request, id)

#Aquí se ve la api creada en forma de Clases
# class DataAPIView(APIView):
#
# 	def get(self, request):
# 		data = Data.objects.all()
# 		serializer = DataSerializer(data, many=True)
# 		return Response(serializer.data)
#
# 	def post(self, request):
# 		serializer = DataSerializer(data=request.data)
#
# 		if serializer.is_valid():
# 			serializer.save()
# 			return Response(serializer.data, status=status.HTTP_201_CREATED)
# 		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
# class DataDetails(APIView):
#
# 	def get_object(self, id):
# 		try:
# 			return Data.objects.get(id=id)
#
# 		except Data.DoesNotExist:
# 			return HttpResponse(status=status.HTTP_404_NOT_FOUND)
#
# 	def get(self, request, id):
# 		data = self.get_object(id)
# 		serializer = DataSerializer(data)
# 		return Response(serializer.data)
#
# 	def put(self, request, id):
# 		data = self.get_object(id)
# 		serializer = DataSerializer(data, data=request.data)
# 		if serializer.is_valid():
# 			serializer.save()
# 			return Response(serializer.data)
# 		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
# 	def delete(self, request, id):
# 		data = self.get_object(id)
# 		data.delete()
# 		return Response(status=status.HTTP_204_NO_CONTENT)
#
#
#
# #esta es la vista de la carga en la api en forma de funciones
# @api_view(['GET', 'POST'])
# def data_list(request):
# 	if request.method == 'GET':
# 		data = Data.objects.all()
# 		serializer = DataSerializer(data, many=True)
# 		return Response(serializer.data)
#
# 	elif request.method == 'POST':
# 		serializer = DataSerializer(data=request.data)
#
# 		if serializer.is_valid():
# 			serializer.save()
# 			return Response(serializer.data, status=status.HTTP_201_CREATED)
# 		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
# @api_view(['GET', 'PUT', 'DELETE'])
# def data_detail(request, pk):
# 	try:
# 		data = Data.objects.get(pk=pk)
#
# 	except Data.DoesNotExist:
# 		return HttpResponse(status=status.HTTP_404_NOT_FOUND)
#
# 	if request.method == 'GET':
# 		serializer = DataSerializer(data)
# 		return Response(serializer.data)
#
# 	elif request.method == 'PUT':
# 		serializer = DataSerializer(data, data=request.data)
# 		if serializer.is_valid():
# 			serializer.save()
# 			return Response(serializer.data)
# 		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
# 	elif request.method == 'DELETE':
# 		data.delete()
# 		return Response(status=status.HTTP_204_NO_CONTENT)




