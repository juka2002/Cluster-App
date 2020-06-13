from django.shortcuts import render
from .models import Data
from .resources import DataResource
from django.contrib import messages
from tablib import Dataset
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from api.serializers import DataSerializer
import pandas as pd

# Create your views here.

#esta es la vista de carga de la data en excel
def simple_upload(request):
	if request.method == 'POST':
		data_resource = DataResource()
		dataset = Dataset()
		new_person = request.FILES['myfile']

		if not new_person.name.endswith('xlsx'):
			messages.info(request, 'formato incorrecto')
			return render(request, 'base.html')

		imported_data = dataset.load(new_person.read(), format='xlsx')
		for data in imported_data:
			value = Data(
				data[0],
				data[1],
				data[2],
				data[3],
				data[4],
				data[5],
				data[6],
				)
			value.save()
	return	render(request,'base.html')

#esta es la vista de la carga en la api
def data_list(request):
	if request.method == 'GET':
		data = Data.objects.all()
		serializer = DataSerializer(data, many=True)
		return JsonResponse(serializer.data, safe=False)

	elif request.method == 'POST':
		data = JSONParser.parse(request)
		serializer = DataSerializer(data=data)

		if serializer.is_valid():
			serializer.save()
			return JsonResponse(serializer.data, status=201)

		return JsonResponse(serializer.errors, status=400)
