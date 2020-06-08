from django.shortcuts import render
from .models import Data
from .resources import DataResource
from django.contrib import messages
from tablib import Dataset
from django.http import HttpResponse

# Create your views here.
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